import os
from datetime import datetime

from database.models import Room, User, Wallet
from routes.utils import contract_logic
from routes.utils.smart_contract import CryptoUtils, Decision, Party
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from ..utils.ai_arbiter import AIVerifier, TransactionClassifier
from .redis_manager import RedisConnectionManager


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
    """Handles the locking of the buyers funds and CREATES the contract."""
    if user.id != room.buyer_id or room.status != "AWAITING PAYMENT":
        return

    # 1. Create the contract dictionary using the new stateless function
    #    (Assuming public keys are stored as hex strings in your models)
    new_contract = contract_logic.create_contract(
        room.buyer_id,
        room.seller_id,
        room.amount,
        room.buyer_public_key,  # Expects hex string
        room.seller_public_key,  # Expects hex string
        room.ai_public_key,  # Expects hex string
    )

    # 2. Store the entire contract state in the Room model
    #    (Your Room model needs a JSON column, e.g., `contract = Column(JSON)`)
    room.contract = new_contract
    flag_modified(room, "contract")  # Important for JSON columns

    # Update wallet and room status
    user_wallet = db.query(Wallet).filter_by(user_id=user.id).first()
    user_wallet.balance -= room.amount
    user_wallet.locked += room.amount
    room.status = "MONEY_SECURED"

    db.commit()

    await broadcast_state_update(room)


async def handle_confirm_product_delivered(
    room: Room, user: User, data: dict, db: Session
):
    """Handles the Seller confirming he delivered the product"""
    if user.id != room.seller_id or room.status != "MONEY_SECURED":
        print(
            f"Unauthorized delivery confirmation attempt by user {user.id} in room {room.room_phrase}.",
            f"{user.id != room.seller_id}",
            f"{room.status != "MONEY_SECURED"}",
        )
        return

    signed_message = data.get("signed_message")

    print(
        f"Received raw signed_message: '{signed_message}' length: {len(signed_message)}"
    )

    if not signed_message:
        print("Signed message missing")
        return

    try:
        updated_contract = contract_logic.sign(
            room.contract,
            Party.SELLER,
            Decision.RELEASE_TO_SELLER,
            signed_message,
        )
    except ValueError as e:
        print(f"Signature failed: {e}")
        return

    room.status = "PRODUCT DELIVERED"
    room.contract = updated_contract
    flag_modified(room, "contract")

    # Check if the contract was completed by the last signature
    if updated_contract["status"] == "COMPLETED":
        recipient_id = updated_contract["released_to"]
        recipient_wallet = db.query(Wallet).filter_by(user_id=recipient_id).first()
        buyer_wallet = db.query(Wallet).filter_by(user_id=room.buyer_id).first()

        buyer_wallet.locked -= room.amount
        recipient_wallet.balance += room.amount

        room.status = "TRANSACTION SUCCESSFULL"

    db.commit()
    await broadcast_state_update(room)


async def handle_transaction_successfull(
    room: Room, user: User, data: dict, db: Session
):
    """Handles the successful transaction by signing the contract."""
    if user.id != room.buyer_id or room.status != "PRODUCT DELIVERED":
        print(
            "WRONG",
            f"{user.id != room.buyer_id}",
            f"{room.status != "PRODUCT DELIVERED"}",
        )
        return

    signature_hex = data.get(
        "signed_message"
    )  # Client should send signature as a hex string
    if not signature_hex:
        print("Sgnhex")
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
    except ValueError as e:
        print(f"Signature failed: {e}")
        return

    # 3. Save the new state back to the database
    room.contract = updated_contract
    flag_modified(room, "contract")

    # Check if the contract was completed by the last signature
    if updated_contract["status"] == "COMPLETED":
        recipient_id = updated_contract["released_to"]
        recipient_wallet = db.query(Wallet).filter_by(user_id=recipient_id).first()
        buyer_wallet = db.query(Wallet).filter_by(user_id=room.buyer_id).first()

        buyer_wallet.locked -= room.amount
        recipient_wallet.balance += room.amount

        room.status = "COMPLETE"

    db.commit()
    await broadcast_state_update(room)


async def handle_initiate_dispute(room: Room, user: User, data: dict, db: Session):
    """Handles the Buyer initiating a dispute."""
    if user.id != room.buyer_id or room.status != "PRODUCT DELIVERED":
        print(
            "Unauthorized or invalid state for dispute",
            f"{user.id != room.buyer_id}",
            f"{room.status != "PRODUCT DELIVERED"}",
        )
        return

    classifier = TransactionClassifier()
    classification = await classifier.classify(room.description)

    room.dispute_status = "AWAITING_EVIDENCE"
    room.required_evidence = classification.get("required_evidence", [])
    room.status = "DISPUTE"
    db.commit()

    await broadcast_state_update(room)


async def handle_finalize_submission(room: Room, user: User, data: dict, db: Session):
    """Handles the Seller finalizing their evidence submission, triggering AI review."""
    if user.id != room.seller_id or room.dispute_status != "AWAITING_EVIDENCE":
        return

    # TODO: Check if all required_evidence has been submitted
    room.dispute_status = "IN_REVIEW"
    db.commit()
    await broadcast_state_update(room)

    verifier = AIVerifier()
    transaction_details = {"description": room.description, "amount": room.amount}
    final_verdict = await verifier.verify_evidence(
        transaction_details, room.submitted_evidence
    )

    room.ai_verdict = final_verdict
    room.dispute_status = "RESOLVED"
    flag_modified(room, "ai_verdict")

    ai_decision = final_verdict.get("decision")
    if ai_decision == "APPROVE":
        contract_decision = Decision.RELEASE_TO_SELLER
    else:
        contract_decision = Decision.REFUND_TO_BUYER

    ai_private_key_hex = room.private_key
    ai_private_key_bytes = bytes.fromhex(ai_private_key_hex)

    contract_dict = room.contract
    message_to_sign = f"{contract_dict['contract_id']}:{Party.AI_ORACLE.value}:{contract_decision.value}"

    ai_signature = CryptoUtils().sign_message(message_to_sign, ai_private_key_bytes)
    ai_signature_hex = ai_signature.hex()

    updated_contract = contract_logic.sign(
        contract_dict, Party.AI_ORACLE, contract_decision, ai_signature_hex
    )
    room.contract = updated_contract
    flag_modified(room, "contract")

    if updated_contract["status"] == "COMPLETED":
        recipient_id = updated_contract["released_to"]
        recipient_wallet = db.query(Wallet).filter_by(user_id=recipient_id).first()
        buyer_wallet = db.query(Wallet).filter_by(user_id=room.buyer_id).first()

        buyer_wallet.locked -= room.amount
        recipient_wallet.balance += room.amount

        room.status = "COMPLETE"

    db.commit()
    await broadcast_state_update(room)
