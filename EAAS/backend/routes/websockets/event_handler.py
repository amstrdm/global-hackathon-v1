from datetime import datetime

from database.models import Room, User, Wallet
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from .redis_manager import RedisConnectionManager


async def broadcast_state_update(room: Room):
    """Constructs and broadcasts the current state of the room to all clients."""
    manager = RedisConnectionManager()
    state_update_message = {
        "type": "description_state_update",
        "description": room.description,
        "status": room.status,
        "escrow_address": room.escrow_address,
    }
    await manager.broadcast_to_room(str(room.room_phrase), state_update_message)


async def handle_chat_message(room: Room, user: User, data: dict, db: Session):
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


async def handle_propose_description(room: Room, user: User, data: dict, db: Session):
    """Handles the buyer's initial description proposal."""
    if user.id != room.buyer_id or room.status != "AWAITING_DESCRIPTION":
        print(
            f"Unauthorized proposal attempt by user {user.id} in room {room.room_phrase}."
        )
        return

    description_text = data.get("description", "").strip()
    if not description_text:
        return

    room.description = description_text
    room.status = "AWAITING_SELLER_APPROVAL"

    db.commit()

    await broadcast_state_update(room)


async def handle_approve_description(room: Room, user: User, data: dict, db: Session):
    """Handles a user approving the current description, ending the negotiation
    and moving to the next state.
    """

    is_seller_approving = (
        user.id == room.seller_id and room.status == "AWAITING_SELLER_APPROVAL"
    )
    is_buyer_approving = (
        user.id == room.buyer_id and room.status == "AWAITING_BUYER_APPROVAL"
    )

    if not (is_seller_approving or is_buyer_approving):
        print(
            f"Unauthorized approval attempt by user {user.id} in room {room.room_phrase}."
        )
        return

    room.status = "AWAITING_SELLER_READY"
    db.commit()
    print(f"Description approved in room {room.room_phrase}. New status: {room.status}")

    await broadcast_state_update(room)


async def handle_edit_description(room: Room, user: User, data: dict, db: Session):
    """
    Handles a description edit from either the seller or the buyer,
    depending on whose turn it is.
    """

    is_seller_turn = (
        user.id == room.seller_id and room.status == "AWAITING_SELLER_APPROVAL"
    )
    is_buyer_turn = (
        user.id == room.buyer_id and room.status == "AWAITING_BUYER_APPROVAL"
    )

    if not (is_seller_turn or is_buyer_turn):
        print(
            f"Unauthorized edit attempt by user {user.id} in room {room.room_phrase}."
        )
        return

    new_description = data.get("description", "").strip()
    if not new_description:
        return

    room.description = new_description
    if is_seller_turn:
        room.status = "AWAITING_BUYER_APPROVAL"
    elif is_buyer_turn:
        room.status = "AWAITING_SELLER_APPROVAL"

    db.commit()

    await broadcast_state_update(room)


async def handle_confirm_seller_ready(room: Room, user: User, data: dict, db: Session):
    """Handles the Seller confirming hes ready to deliver & receive the money"""
    if user.id != room.seller_id or room.status != "AWAITING_SELLER_READY":
        print(
            f"Unauthorized ready attempt by user {user.id} in room {room.room_phrase}."
        )
        return

    room.status = "AWAITING PAYMENT"
    db.commit()

    await broadcast_state_update(room)


async def handle_lock_funds(room: Room, user: User, data: dict, db: Session):
    """Handles the locking of the buyers funds"""
    if user.id != room.buyer_id or room.status != "AWAITING PAYMENT":
        print(
            f"Unauthorized locking attempt by user {user.id} in room {room.room_phrase}.",
            f"{user.id != room.buyer_id}",
            f"{room.status != "AWAITING PAYMENT"}",
        )
        return

    user_wallet = db.query(Wallet).filter_by(user_id=user.id).first()

    if not user_wallet:
        print("Wallet missing???")
        raise
    user_wallet.balance -= room.amount
    user_wallet.locked += room.amount

    room.status = "MONEY_SECURED"
    db.commit()

    await broadcast_state_update(room)
