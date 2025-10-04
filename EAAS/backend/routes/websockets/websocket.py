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
from sqlalchemy.orm.attributes import flag_modified

from ..rooms.utils import room_to_dict
from .handle_connections import ConnectionManager

router = APIRouter()


@router.websocket("/ws/{room_phrase}/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket, room_phrase: str, user_id: str, db: Session = Depends(get_db)
):
    """WebSocket connection for real time updates"""
    is_connected = await ConnectionManager.connect(websocket, room_phrase)

    if not is_connected:
        return

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

        join_message = {
            "type": "admin_message",
            "sender_id": user_id,
            "sender_username": username,
            "message": f"{user.role or 'User'} '{username}' joined the room",
            "timestamp": datetime.now().isoformat(),
        }
        room.messages.append(join_message)
        flag_modified(room, "messages")
        db.commit()
        await ConnectionManager.broadcast_to_room(room_phrase, join_message)

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
                    flag_modified(room, "messages")
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
        if "user" in locals() and user:
            leave_message = {
                "type": "admin_message",
                "buyer_id": user_id,
                "buyer_username": username,
                "message": f"{user.role} {username} left the room",
                "timestamp": datetime.now().isoformat(),
            }
            room.messages.append(leave_message)
            flag_modified(room, "messages")
            db.commit()
            await ConnectionManager.broadcast_to_room(room_phrase, leave_message)
