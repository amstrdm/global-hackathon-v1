import json
from datetime import datetime

from database.db import get_db
from database.models import Room, User
from fastapi import (
    APIRouter,
    Depends,
    WebSocket,
    WebSocketDisconnect,
    WebSocketException,
    status,
)
from sqlalchemy.orm import Session

from ..rooms.utils import room_to_dict
from .handle_connections import ConnectionManager

router = APIRouter()


@router.websocket("/ws/{room_phrase}/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket, room_phrase: str, user_id: str, db: Session = Depends(get_db)
):
    """WebSocket connection for real time updates"""
    await ConnectionManager.connect(websocket, room_phrase)

    try:
        # Send initial state
        room = db.query(Room).filter_by(room_phrase=room_phrase).first()
        if not room:
            raise WebSocketException(
                code=status.WS_1008_POLICY_VIOLATION, reason="Room not found"
            )

        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            raise WebSocketException(
                code=status.WS_1008_POLICY_VIOLATION, reason="User not found"
            )

        await websocket.send_json(
            {"type": "connected", "room": room_to_dict(room), "user_id": user_id}
        )

        username = user.username

        while True:
            try:
                data = await websocket.receive_json()
                message_type = data.get("type")

                if message_type == "chat_message":
                    message_obj = {
                        "type": "chat_message",
                        "sender_id": user_id,
                        "sender_username": username,
                        "message": data["message"],
                        "timestamp": datetime.now().isoformat(),
                    }

                    room.messages.append(message_obj)
                    db.commit()
                    await ConnectionManager.broadcast_to_room(room_phrase, message_obj)
                elif message_type == "ping":
                    await websocket.send_json({"type": "pong"})
            except json.JSONDecodeError:
                await websocket.send_json(
                    {"type": "error", "detail": "Invalid JSON format"}
                )
                continue

            except KeyError:
                continue

    except WebSocketDisconnect:
        ConnectionManager.disconnect(websocket, room_phrase)
        if user:
            message_obj = {
                "type": "admin_message",
                "buyer_id": user_id,
                "buyer_username": username,
                "message": f"{user.role} {username} left the room",
                "timestamp": datetime.now().isoformat(),
            }
