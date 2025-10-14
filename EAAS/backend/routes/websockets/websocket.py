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
from utils.logging_config import get_logger

from ..utils.utils import room_to_dict
from . import event_handler
from .redis_manager import RedisConnectionManager

logger = get_logger("routes.websockets.websocket")
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


async def send_websocket_error(
    websocket: WebSocket, error_code: int, reason: str, log_message: str = None
):
    """Helper function to send error and close websocket with proper logging"""
    if log_message:
        logger.warning(log_message)
    try:
        await websocket.close(code=error_code, reason=reason)
    except Exception as e:
        logger.error(f"Error closing websocket: {e}")


@router.websocket("/ws/{room_phrase}/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket, room_phrase: str, user_id: str, db: Session = Depends(get_db)
):
    """WebSocket connection for real time updates with comprehensive error handling and logging"""
    logger.info(f"WebSocket connection attempt - Room: {room_phrase}, User: {user_id}")

    manager = RedisConnectionManager()
    is_fully_connected = False
    user = None
    room = None
    wallet = None

    try:
        # Validate input parameters
        if not room_phrase or not room_phrase.strip():
            await send_websocket_error(
                websocket,
                status.WS_1008_POLICY_VIOLATION,
                "Invalid room phrase",
                "Empty room phrase provided for websocket connection",
            )
            return

        if not user_id or not user_id.strip():
            await send_websocket_error(
                websocket,
                status.WS_1008_POLICY_VIOLATION,
                "Invalid user ID",
                "Empty user ID provided for websocket connection",
            )
            return

        # Accept the websocket connection
        await websocket.accept()
        logger.debug(
            f"WebSocket connection accepted for user {user_id} in room {room_phrase}"
        )

        # Fetch required data from database
        try:
            room = db.query(Room).filter_by(room_phrase=room_phrase).first()
            user = db.query(User).filter_by(id=user_id).first()
            wallet = db.query(Wallet).filter_by(user_id=user_id).first()
        except Exception as e:
            logger.error(f"Database error during websocket connection: {e}")
            await send_websocket_error(
                websocket,
                status.WS_1011_INTERNAL_ERROR,
                "Database error",
                f"Database error during websocket connection: {e}",
            )
            return

        # Validate room exists
        if not room:
            await send_websocket_error(
                websocket,
                status.WS_1008_POLICY_VIOLATION,
                "Room not found",
                f"Room not found: {room_phrase}",
            )
            return

        # Validate user exists
        if not user:
            await send_websocket_error(
                websocket,
                status.WS_1008_POLICY_VIOLATION,
                "User not found",
                f"User not found: {user_id}",
            )
            return

        # Validate wallet exists
        if not wallet:
            await send_websocket_error(
                websocket,
                status.WS_1008_POLICY_VIOLATION,
                "No wallet found",
                f"No wallet found for user: {user_id}",
            )
            return

        logger.debug(
            f"User {user.username} ({user.role}) attempting to connect to room {room_phrase}"
        )

        # Role-based authorization and room joining logic
        if user.role == "BUYER":
            if room.buyer_id is None:
                # New buyer joining
                if room.amount > wallet.balance:
                    await send_websocket_error(
                        websocket,
                        status.WS_1008_POLICY_VIOLATION,
                        "Insufficient balance",
                        f"Buyer {user_id} has insufficient balance: {wallet.balance} < {room.amount}",
                    )
                    return

                try:
                    room.buyer_id = user.id
                    room.buyer_public_key = user.public_key
                    room.status = "AWAITING_DESCRIPTION"
                    db.commit()
                    db.refresh(room)
                    logger.info(f"Buyer {user.username} joined room {room_phrase}")
                except Exception as e:
                    logger.error(f"Error updating room for new buyer: {e}")
                    await send_websocket_error(
                        websocket,
                        status.WS_1011_INTERNAL_ERROR,
                        "Database error",
                        f"Error updating room for new buyer: {e}",
                    )
                    return

            elif room.buyer_id != user.id:
                await send_websocket_error(
                    websocket,
                    status.WS_1008_POLICY_VIOLATION,
                    "Room occupied",
                    f"Buyer {user_id} attempted to join occupied room {room_phrase} (buyer: {room.buyer_id})",
                )
                return

        elif user.role == "SELLER":
            if room.seller_id != user.id:
                await send_websocket_error(
                    websocket,
                    status.WS_1008_POLICY_VIOLATION,
                    "Unauthorized seller",
                    f"Seller {user_id} attempted to join room {room_phrase} owned by {room.seller_id}",
                )
                return
        else:
            await send_websocket_error(
                websocket,
                status.WS_1008_POLICY_VIOLATION,
                "Invalid role",
                f"Invalid user role: {user.role}",
            )
            return

        # Before attempting to connect, check for and remove any stale connections
        # for this user in this room. This handles fast page reloads.
        is_participant = (user.id == room.buyer_id) or (user.id == room.seller_id)
        if is_participant:
            current_user_ids_in_room = await manager.get_connections_in_room(
                room_phrase
            )
            if user_id in current_user_ids_in_room:
                logger.info(
                    f"Reconnection attempt by user {user_id}. Clearing stale session."
                )
                await manager.remove_user_from_room(room_phrase, user_id)

        # Connect to Redis manager
        try:
            if not await manager.connect(websocket, room_phrase, user_id):
                await send_websocket_error(
                    websocket,
                    status.WS_1008_POLICY_VIOLATION,
                    "Room full",
                    f"Room {room_phrase} is full, cannot accept user {user_id}",
                )
                return
        except Exception as e:
            logger.error(f"Redis connection error: {e}")
            await send_websocket_error(
                websocket,
                status.WS_1011_INTERNAL_ERROR,
                "Connection error",
                f"Redis connection error: {e}",
            )
            return

        # Send initial connection data
        try:
            room_data = room_to_dict(room)
            await websocket.send_json(
                {"type": "connected", "room": room_data, "user_id": user_id}
            )
            logger.debug(f"Sent connection data to user {user_id}")
        except Exception as e:
            logger.error(f"Error sending connection data: {e}")
            await send_websocket_error(
                websocket,
                status.WS_1011_INTERNAL_ERROR,
                "Connection error",
                f"Error sending connection data: {e}",
            )
            return

        # Create and broadcast join message
        try:
            join_message = {
                "type": "admin_message",
                "username": user.username,
                "message": f"{user.role or 'User'} '{user.username}' joined the room",
                "timestamp": datetime.now().isoformat(),
            }
            room.messages.append(join_message)
            flag_modified(room, "messages")
            db.commit()
            await manager.broadcast_to_room(room_phrase, join_message)
            logger.info(f"User {user.username} joined room {room_phrase}")
        except Exception as e:
            logger.error(f"Error broadcasting join message: {e}")
            # Don't fail the connection for this, just log it

        is_fully_connected = True

        # Main message handling loop
        while True:
            try:
                data = await websocket.receive_json()
                message_type = data.get("type")
                logger.debug(
                    f"Received message type '{message_type}' from user {user_id}"
                )

                handler = ACTION_DISPATCHER.get(message_type)
                if handler:
                    try:
                        db.refresh(room)
                        await handler(room, user, data, db)
                        logger.debug(
                            f"Successfully handled {message_type} from user {user_id}"
                        )
                    except Exception as e:
                        logger.error(
                            f"Error handling {message_type} from user {user_id}: {e}"
                        )
                        # Send error to client
                        await websocket.send_json(
                            {
                                "type": "error",
                                "message": f"Error processing {message_type}: {str(e)}",
                                "original_type": message_type,
                            }
                        )
                else:
                    logger.warning(
                        f"Unknown message type '{message_type}' from user {user_id}"
                    )
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": f"Unknown message type: {message_type}",
                            "original_type": message_type,
                        }
                    )

            except WebSocketDisconnect:
                logger.info(f"User {user_id} disconnected from room {room_phrase}")
                break

            except RuntimeError as e:
                if 'Cannot call "receive"' in str(e):
                    logger.info(f"WebSocket receive error for user {user_id}: {e}")
                    break
                else:
                    logger.error(f"Unexpected RuntimeError for user {user_id}: {e}")
                    raise e

            except json.JSONDecodeError as e:
                logger.warning(f"Malformed JSON received from user {user_id}: {e}")
                await websocket.send_json(
                    {"type": "error", "message": "Invalid JSON format"}
                )
                continue

            except KeyError as e:
                logger.warning(f"Missing key in message from user {user_id}: {e}")
                await websocket.send_json(
                    {"type": "error", "message": f"Missing required field: {str(e)}"}
                )
                continue

            except Exception as e:
                logger.error(
                    f"Unexpected error processing message from user {user_id}: {e}"
                )
                await websocket.send_json(
                    {"type": "error", "message": "An internal server error occurred"}
                )
                continue

    except Exception as e:
        logger.error(f"Critical error in websocket endpoint for user {user_id}: {e}")
        try:
            await websocket.close(
                code=status.WS_1011_INTERNAL_ERROR, reason="Internal server error"
            )
        except:
            pass

    finally:
        # Cleanup logic
        try:
            if is_fully_connected and user and room:
                leave_message = {
                    "type": "admin_message",
                    "username": user.username,
                    "message": f"{user.role} {user.username} left the room",
                    "timestamp": datetime.now().isoformat(),
                }

                try:
                    db.refresh(room)
                    room.messages.append(leave_message)
                    flag_modified(room, "messages")
                    db.commit()
                    await manager.broadcast_to_room(room_phrase, leave_message)
                    logger.info(f"User {user.username} left room {room_phrase}")
                except Exception as e:
                    logger.error(f"Error broadcasting leave message: {e}")

            # Disconnect from Redis manager
            if user:
                try:
                    await manager.disconnect(websocket, room_phrase, str(user.id))
                    logger.debug(f"Cleaned up connection for user {user.id}")
                except Exception as e:
                    logger.error(f"Error during cleanup for user {user.id}: {e}")

        except Exception as e:
            logger.error(f"Error during websocket cleanup: {e}")
