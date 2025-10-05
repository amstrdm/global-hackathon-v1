import json
from datetime import datetime

from database.db import get_db
from database.models import Room, User, Wallet
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
from .redis_manager import RedisConnectionManager

router = APIRouter()

ACTION_DISPATCHER = {
    "chat_message": event_handler.handle_chat_message,
    "propose_description": event_handler.handle_propose_description,
    "approve_description": event_handler.handle_approve_description,
    "edit_description": event_handler.handle_edit_description,
    "confirm_seller_ready": event_handler.handle_confirm_seller_ready,
    "buyer_lock_funds": event_handler.handle_lock_funds,
    "product_delivered": event_handler.handle_confirm_product_delivered,
    "transaction_successfull": event_handler.handle_transaction_successfull,
    "init_dispute": event_handler.handle_initiate_dispute,
    "finalize_submission": event_handler.handle_finalize_submission,
}


@router.websocket("/ws/{room_phrase}/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket, room_phrase: str, user_id: str, db: Session = Depends(get_db)
):
    """WebSocket connection for real time updates"""
    manager = RedisConnectionManager()
    is_fully_connected = False

    await websocket.accept()

    room = db.query(Room).filter_by(room_phrase=room_phrase).first()
    user = db.query(User).filter_by(id=user_id).first()
    wallet = db.query(Wallet).filter_by(user_id=user_id).first()

    if not room:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION, reason="Room not found"
        )
        return

    if not user:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION, reason="User not found"
        )
        return

    print(user.role)

    if user.role == "BUYER":
        if room.buyer_id is None:
            room.buyer_id = user.id
            room.buyer_public_key = user.public_key
            room.status = "AWAITING_DESCRIPTION"
            db.commit()
            db.refresh(room)
        elif room.buyer_id != user.id:
            await websocket.close(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="Room already has a buyer",
            )
            return
        elif room.amount > wallet.balance:
            await websocket.close(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="Your Balance is too low to partake in this transaction",
            )
            return

    elif user.role == "SELLER":
        if room.seller_id != user.id:
            await websocket.close(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="You are not the seller of this room",
            )
            return
    else:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION, reason="Invalid user role"
        )
        return

    if not await manager.connect(websocket, room_phrase, user_id):
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION, reason="Room is full"
        )

    username = user.username

    try:
        print(room_to_dict(room))
        await websocket.send_json(
            {"type": "connected", "room": room_to_dict(room), "user_id": user_id}
        )

        join_message = {
            "type": "admin_message",
            "username": username,
            "message": f"{user.role or 'User'} '{username}' joined the room",
            "timestamp": datetime.now().isoformat(),
        }
        room.messages.append(join_message)
        flag_modified(room, "messages")
        db.commit()
        await manager.broadcast_to_room(room_phrase, join_message)

        is_fully_connected = True

        while True:
            try:
                data = await websocket.receive_json()
                message_type = data.get("type")

                handler = ACTION_DISPATCHER.get(message_type)
                if handler:
                    db.refresh(room)
                    await handler(room, user, data, db)
                else:
                    await websocket.close(
                        code=status.WS_1008_POLICY_VIOLATION,
                        reason="Unknown message type",
                    )
                    return

            except (WebSocketDisconnect, RuntimeError) as e:
                if isinstance(e, WebSocketDisconnect) or 'Cannot call "receive"' in str(
                    e
                ):
                    print(f"Client {user_id} disconnected from room {room_phrase}.")
                    break
                else:
                    # If it's a different RuntimeError, re-raise it.
                    raise e

            except (json.JSONDecodeError, KeyError):
                # Ignore malformed messages and continue listening.
                print(f"Received malformed JSON from {user_id}.")
                continue

            except Exception as e:
                # Handle other unexpected errors during message processing.
                print(
                    f"An unexpected error occurred while processing message in room {room_phrase}: {e}"
                )
                # Optionally, notify the client about the specific error.
                await websocket.send_json(
                    {"type": "error", "message": "An internal server error occurred."}
                )
                continue

    finally:
        # This logic now runs only once upon disconnection.
        if is_fully_connected and user and room:
            leave_message = {
                "type": "admin_message",
                "username": username,
                "message": f"{user.role} {username} left the room",
                "timestamp": datetime.now().isoformat(),
            }
            # Use a fresh session or refresh the object in case of long-running connections
            db.refresh(room)
            room.messages.append(leave_message)
            flag_modified(room, "messages")
            db.commit()
            await manager.broadcast_to_room(room_phrase, leave_message)

        # This is the final cleanup step.
        if user:
            await manager.disconnect(websocket, room_phrase, str(user.id))
            print(f"Successfully cleaned up connection for user {user.id}")
