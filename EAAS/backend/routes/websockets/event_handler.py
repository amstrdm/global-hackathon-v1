from datetime import datetime

from database.models import Room
from sqlalchemy.orm.attributes import flag_modified

from .handle_connections import ConnectionManager


async def handle_propose_description():
    pass


async def handle_chat_message(room, user, data, db):
    """
    Validates, persists, and broadcasts a user chat message.
    """
    message_content = data.get("message")
    if not isinstance(message_content, str) or not message_content.strip():
        return

    message_obj = {
        "type": "chat_message",
        "sender_id": str(user.id),
        "sender_username": user.username,
        "message": message_content,
        "timestamp": datetime.now().isoformat(),
    }

    room.messages.append(message_obj)
    flag_modified(room, "messages")
    db.commit()

    await ConnectionManager.broadcast_to_room(room.room_phrase, message_obj)
