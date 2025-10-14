import os
from datetime import datetime

from database.models import Room, User, Wallet
from dotenv import load_dotenv
from routes.utils import contract_logic
from routes.utils.smart_contract import CryptoUtils, Decision, Party
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from utils.logging_config import get_logger

from ..utils import contract_logic
from ..utils.ai_arbiter import AIVerifier, TransactionClassifier
from .redis_manager import RedisConnectionManager

logger = get_logger("routes.websockets.event_handler")

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
env_path = os.path.join(project_root, ".env")
load_dotenv(env_path)


async def broadcast_state_update(room: Room):
    """Constructs and broadcasts the current state of the room to all clients."""
    manager = RedisConnectionManager()
    if room.status == "DISPUTE":
        state_update_message = {
            "type": "state_update",
            "description": room.description,
            "dispute_status": room.dispute_status,
            "required_evidence": room.required_evidence,
            "submitted_evidence": room.submitted_evidence,
            "ai_verdict": room.ai_verdict,
            "contract": room.contract,
        }
    else:
        state_update_message = {
            "type": "state_update",
            "description": room.description,
            "status": room.status,
            "escrow_address": room.escrow_address,
            "contract": room.contract,
        }
    await manager.broadcast_to_room(str(room.room_phrase), state_update_message)


async def handle_chat_message(room: Room, user: User, data: dict, db: Session):
    """
    Validates, persists, and broadcasts a user chat message.
    """
    manager = RedisConnectionManager()
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

    await manager.broadcast_to_room(room.room_phrase, message_obj)


async def handle_propose_description(room: Room, user: User, data: dict, db: Session):
    """Handles the buyer's initial description proposal."""
    logger.info(f"Description proposal attempt - Room: {room.room_phrase}, User: {user.username}")
    
    if user.id != room.buyer_id or room.status != "AWAITING_DESCRIPTION":
        logger.warning(f"Unauthorized proposal attempt by user {user.id} in room {room.room_phrase}")
        return

    description_text = data.get("description", "").strip()
    if not description_text:
        logger.warning(f"Empty description provided by user {user.id}")
        return

    try:
        room.description = description_text
        room.status = "AWAITING_SELLER_APPROVAL"
        db.commit()
        logger.info(f"Description proposed by buyer {user.username} in room {room.room_phrase}")
        await broadcast_state_update(room)
    except Exception as e:
        logger.error(f"Error updating room description: {e}")
        raise


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
        logger.warning(f"Unauthorized approval attempt by user {user.id} in room {room.room_phrase}")
        return

    try:
        room.status = "AWAITING_SELLER_READY"
        db.commit()
        logger.info(f"Description approved in room {room.room_phrase}. New status: {room.status}")
        await broadcast_state_update(room)
    except Exception as e:
        logger.error(f"Error approving description: {e}")
        raise


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
        logger.warning(f"Unauthorized edit attempt by user {user.id} in room {room.room_phrase}")
        return

    new_description = data.get("description", "").strip()
    if not new_description:
        logger.warning(f"Empty description provided by user {user.id}")
        return

    try:
        room.description = new_description
        if is_seller_turn:
            room.status = "AWAITING_BUYER_APPROVAL"
        elif is_buyer_turn:
            room.status = "AWAITING_SELLER_APPROVAL"

        db.commit()
        logger.info(f"Description edited by {user.username} in room {room.room_phrase}")
        await broadcast_state_update(room)
    except Exception as e:
        logger.error(f"Error editing description: {e}")
        raise


async def handle_confirm_seller_ready(room: Room, user: User, data: dict, db: Session):
    """Handles the Seller confirming hes ready to deliver & receive the money"""
    if user.id != room.seller_id or room.status != "AWAITING_SELLER_READY":
        logger.warning(f"Unauthorized ready attempt by user {user.id} in room {room.room_phrase}")
        return

    try:
        room.status = "AWAITING_PAYMENT"
        db.commit()
        logger.info(f"Seller {user.username} confirmed ready in room {room.room_phrase}")
        await broadcast_state_update(room)
    except Exception as e:
        logger.error(f"Error confirming seller ready: {e}")
        raise


async def handle_lock_funds(room: Room, user: User, data: dict, db: Session):
    """Handles the locking of the buyers funds and CREATES the contract."""
    logger.info(f"Fund locking attempt - Room: {room.room_phrase}, User: {user.username}")
    
    if user.id != room.buyer_id or room.status != "AWAITING_PAYMENT":
        logger.warning(f"Unauthorized fund locking attempt by user {user.id} in room {room.room_phrase}")
        return

    try:
        # 1. Create the contract dictionary using the new stateless function
        logger.debug(f"Creating contract for room {room.room_phrase}")
        new_contract = contract_logic.create_contract(
            room.buyer_id,
            room.seller_id,
            room.amount,
            room.buyer_public_key,  # Expects hex string
            room.seller_public_key,  # Expects hex string
            room.ai_public_key,  # Expects hex string
        )

        # 2. Store the entire contract state in the Room model
        room.contract = new_contract
        flag_modified(room, "contract")  # Important for JSON columns

        # Update wallet and room status
        user_wallet = db.query(Wallet).filter_by(user_id=user.id).first()
        if not user_wallet:
            logger.error(f"Wallet not found for user {user.id}")
            raise ValueError("User wallet not found")
        
        if user_wallet.balance < room.amount:
            logger.error(f"Insufficient balance for user {user.id}: {user_wallet.balance} < {room.amount}")
            raise ValueError("Insufficient balance")
        
        user_wallet.balance -= room.amount
        user_wallet.locked += room.amount
        room.status = "MONEY_SECURED"

        db.commit()
        logger.info(f"Funds locked successfully by buyer {user.username} in room {room.room_phrase}")
        await broadcast_state_update(room)
    except Exception as e:
        logger.error(f"Error locking funds: {e}")
        raise


async def handle_confirm_product_delivered(
    room: Room, user: User, data: dict, db: Session
):
    """Handles the Seller confirming he delivered the product"""
    if user.id != room.seller_id or room.status != "MONEY_SECURED":
        logger.warning(f"Unauthorized delivery confirmation attempt by user {user.id} in room {room.room_phrase}")
        return

    signed_message_hex = data.get("signed_message")

    if not signed_message_hex:
        logger.warning("Signed message missing for product delivery confirmation")
        return

    logger.debug(f"Received signed message for product delivery, length: {len(signed_message_hex)}")

    try:
        updated_contract = contract_logic.sign(
            room.contract, Party.SELLER, Decision.RELEASE_TO_SELLER, signed_message_hex
        )
        logger.debug("Contract signature verified successfully")
    except ValueError as e:
        logger.error(f"Signature verification failed: {e}")
        raise

    try:
        # Just update the status directly
        room.status = "PRODUCT_DELIVERED"

        # Create a simple contract update without signature verification
        if room.contract:
            room.contract["seller_signed"] = True
            room.contract["seller_decision"] = "RELEASE_TO_SELLER"
            flag_modified(room, "contract")

        db.commit()
        logger.info(f"Product delivery confirmed by seller {user.username} in room {room.room_phrase}")
        await broadcast_state_update(room)
    except Exception as e:
        logger.error(f"Error confirming product delivery: {e}")
        raise


async def handle_transaction_successfull(
    room: Room, user: User, data: dict, db: Session
):
    """Handles the successful transaction by signing the contract."""
    if user.id != room.buyer_id or room.status != "PRODUCT_DELIVERED":
        logger.warning(f"Unauthorized transaction confirmation attempt by user {user.id} in room {room.room_phrase}")
        return

    signature_hex = data.get(
        "signed_message"
    )  # Client should send signature as a hex string
    if not signature_hex:
        logger.warning("Signed message missing for transaction confirmation")
        return

    # 1. Load the current contract state from the database
    current_contract = room.contract

    # 2. Call the stateless 'sign' function with the current state
    try:
        updated_contract = contract_logic.sign(
            current_contract,
            Party.BUYER,
            Decision.RELEASE_TO_SELLER,
            signature_hex,
        )
        logger.debug("Buyer signature verified successfully")
    except ValueError as e:
        logger.error(f"Signature verification failed: {e}")
        raise

    try:
        # 3. Save the new state back to the database
        room.contract = updated_contract
        flag_modified(room, "contract")

        # Check if the contract was completed by the last signature
        if updated_contract["status"] == "COMPLETED":
            recipient_id = updated_contract["released_to"]
            recipient_wallet = db.query(Wallet).filter_by(user_id=recipient_id).first()
            buyer_wallet = db.query(Wallet).filter_by(user_id=room.buyer_id).first()

            if not recipient_wallet or not buyer_wallet:
                logger.error(f"Wallet not found for transaction completion - recipient: {recipient_id}, buyer: {room.buyer_id}")
                raise ValueError("Wallet not found")

            buyer_wallet.locked -= room.amount
            recipient_wallet.balance += room.amount

            room.status = "COMPLETE"
            logger.info(f"Transaction completed successfully in room {room.room_phrase}")

        db.commit()
        await broadcast_state_update(room)
    except Exception as e:
        logger.error(f"Error completing transaction: {e}")
        raise


async def handle_initiate_dispute(room: Room, user: User, data: dict, db: Session):
    """Handles the Buyer initiating a dispute."""
    if user.id != room.buyer_id or room.status != "PRODUCT_DELIVERED":
        logger.warning(f"Unauthorized dispute initiation attempt by user {user.id} in room {room.room_phrase} (status: {room.status})")
        return

    signature_hex = data.get(
        "signed_message"
    )  # Client should send signature as a hex string
    if not signature_hex:
        logger.warning("Signed message missing for dispute initiation")
        return

    # 1. Load the current contract state from the database
    current_contract = room.contract

    # 2. Call the stateless 'sign' function with the current state
    try:
        updated_contract = contract_logic.sign(
            current_contract,
            Party.BUYER,
            Decision.REFUND_TO_BUYER,
            signature_hex,
        )
        logger.debug("Dispute signature verified successfully")
    except ValueError as e:
        logger.error(f"Signature verification failed for dispute: {e}")
        raise

    try:
        # 3. Save the new state back to the database
        room.contract = updated_contract
        flag_modified(room, "contract")

        # Check if the contract was completed by the last signature
        if updated_contract["status"] == "COMPLETED":
            recipient_id = updated_contract["released_to"]
            recipient_wallet = db.query(Wallet).filter_by(user_id=recipient_id).first()

            if not recipient_wallet:
                logger.error(f"Recipient wallet not found for dispute resolution: {recipient_id}")
                raise ValueError("Recipient wallet not found")

            recipient_wallet.locked -= room.amount
            recipient_wallet.balance += room.amount

            room.status = "COMPLETE"

        db.commit()
        await broadcast_state_update(room)

        # Start AI classification for evidence requirements
        logger.info(f"Starting AI classification for dispute in room {room.room_phrase}")
        classifier = TransactionClassifier()
        classification = await classifier.classify(room.description)

        room.dispute_status = "AWAITING_EVIDENCE"
        room.required_evidence = classification.get("required_evidence", [])
        room.status = "DISPUTE"
        db.commit()

        logger.info(f"Dispute initiated successfully in room {room.room_phrase}")
        await broadcast_state_update(room)
    except Exception as e:
        logger.error(f"Error initiating dispute: {e}")
        raise


async def handle_finalize_submission(room: Room, user: User, data: dict, db: Session):
    """Handles the Seller finalizing their evidence submission, triggering AI review."""
    logger.info(f"Evidence submission finalization triggered - Room: {room.room_phrase}, User: {user.username}")

    if user.id != room.seller_id or room.dispute_status != "AWAITING_EVIDENCE":
        logger.warning(f"Unauthorized evidence finalization attempt by user {user.id} in room {room.room_phrase}")
        return

    try:
        # Update dispute status to in review
        logger.info(f"Updating dispute status from '{room.dispute_status}' to 'IN_REVIEW'")
        room.dispute_status = "IN_REVIEW"
        db.commit()
        await broadcast_state_update(room)
        logger.debug("Broadcasted 'IN_REVIEW' state")

        # Start AI verification
        verifier = AIVerifier()
        transaction_details = {"description": room.description, "amount": room.amount}

        logger.info(f"Starting AI verification for room {room.room_phrase}")
        logger.debug(f"Transaction details: {transaction_details}, Evidence: {room.submitted_evidence}")
        
        final_verdict = await verifier.verify_evidence(
            transaction_details, room.submitted_evidence
        )
        logger.info(f"AI verification completed for room {room.room_phrase}: {final_verdict}")

        # Update room with AI verdict
        room.ai_verdict = final_verdict
        room.dispute_status = "RESOLVED"
        flag_modified(room, "ai_verdict")
        logger.debug("Dispute status updated to 'RESOLVED'")

        # Process AI decision
        ai_decision = final_verdict.get("decision")
        logger.info(f"AI decision: {ai_decision}")
        
        if ai_decision == "APPROVE":
            contract_decision = Decision.RELEASE_TO_SELLER
        else:
            contract_decision = Decision.REFUND_TO_BUYER
        logger.debug(f"Mapped to contract decision: {contract_decision.value}")

        # Sign contract with AI signature
        ai_private_key_pem_string = os.getenv("AI_PRIVATE_KEY")
        if not ai_private_key_pem_string:
            logger.error("AI_PRIVATE_KEY environment variable not set")
            raise ValueError("AI private key not configured")

        ai_private_key_bytes = ai_private_key_pem_string.encode("utf-8")
        contract_dict = room.contract
        
        message_to_sign = f"{contract_dict['contract_id']}:{Party.AI_ORACLE.value}:{contract_decision.value}"
        logger.debug(f"Message for AI to sign: {message_to_sign}")

        ai_signature = CryptoUtils().sign_message(message_to_sign, ai_private_key_bytes)
        ai_signature_hex = ai_signature.hex()
        logger.debug(f"AI signature generated, length: {len(ai_signature_hex)}")

        logger.debug("Applying AI signature to the contract")
        updated_contract = contract_logic.sign(
            contract_dict, Party.AI_ORACLE, contract_decision, ai_signature_hex
        )
        room.contract = updated_contract
        flag_modified(room, "contract")
        logger.debug(f"Contract status after signing: {updated_contract.get('status')}")

        # Process fund transfer if contract is completed
        if updated_contract["status"] == "COMPLETED":
            logger.info("Contract COMPLETED, processing fund transfer")
            recipient_id = updated_contract["released_to"]
            recipient_wallet = db.query(Wallet).filter_by(user_id=recipient_id).first()
            buyer_wallet = db.query(Wallet).filter_by(user_id=room.buyer_id).first()

            if not recipient_wallet or not buyer_wallet:
                logger.error(f"Wallet not found for fund transfer - recipient: {recipient_id}, buyer: {room.buyer_id}")
                raise ValueError("Wallet not found for fund transfer")

            logger.info(f"Transferring ${room.amount} to recipient '{recipient_id}'")
            logger.debug(f"Buyer wallet before: Balance=${buyer_wallet.balance}, Locked=${buyer_wallet.locked}")
            logger.debug(f"Recipient wallet before: Balance=${recipient_wallet.balance}, Locked=${recipient_wallet.locked}")

            buyer_wallet.locked -= room.amount
            recipient_wallet.balance += room.amount

            logger.debug(f"Buyer wallet after: Balance=${buyer_wallet.balance}, Locked=${buyer_wallet.locked}")
            logger.debug(f"Recipient wallet after: Balance=${recipient_wallet.balance}, Locked=${recipient_wallet.locked}")

            room.status = "COMPLETE"
            logger.info("Room status updated to 'COMPLETE'")

        db.commit()
        logger.debug("Final database commit completed")

        await broadcast_state_update(room)
        logger.info(f"Evidence submission finalization completed successfully for room {room.room_phrase}")

    except Exception as e:
        logger.error(f"Error during evidence submission finalization: {e}")
        raise
