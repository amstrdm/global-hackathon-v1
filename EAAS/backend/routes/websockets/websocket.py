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

from ..utils.utils import room_to_dict
from . import event_handler
from .handle_connections import ConnectionManager

router = APIRouter()

ACTION_DISPATCHER = {
    "chat_message": event_handler.handle_chat_message,
    "propose_description": event_handler.handle_propose_description,
}


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
            "username": username,
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

                handler = ACTION_DISPATCHER.get(message_type)

                if handler:
                    await handler(room, user, data, db)
                else:
                    raise WebSocketException(
                        code=status.WS_1008_POLICY_VIOLATION,
                        reason="Unknown message type",
                    )

            except (json.JSONDecodeError, KeyError):
                continue

    except WebSocketDisconnect:
        ConnectionManager.disconnect(websocket, room_phrase)
        if "user" in locals() and user:
            leave_message = {
                "type": "admin_message",
                "username": username,
                "message": f"{user.role} {username} left the room",
                "timestamp": datetime.now().isoformat(),
            }
            room.messages.append(leave_message)
            flag_modified(room, "messages")
            db.commit()
            await ConnectionManager.broadcast_to_room(room_phrase, leave_message)
