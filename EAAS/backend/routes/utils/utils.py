from database.models import Room


def room_to_dict(room: Room) -> dict:
    """Convert Room model to dict"""
    return {
        "room_code": room.room_phrase,
        "seller_id": room.seller_id,
        "buyer_id": room.buyer_id,
        "seller_public_key": room.seller_public_key,
        "buyer_public_key": room.buyer_public_key,
        "ai_public_key": room.ai_public_key,
        "amount": room.amount,
        "description": room.description,
        "required_evidence": room.required_evidence,
        "status": room.status,
        "transaction_id": room.transaction_id,
        "escrow_address": room.escrow_address,
        "shares": room.shares,
        "evidence_submitted": room.evidence_submitted or [],
        "ai_verification_result": room.ai_verification_result,
        "created_at": (
            room.created_at.isoformat()
            if room.created_at is not None
            else room.created_at
        ),
        "buyer_joined_at": (
            room.buyer_joined_at.isoformat()
            if room.buyer_joined_at is not None
            else None
        ),
        "funds_locked_at": (
            room.funds_locked_at.isoformat()
            if room.funds_locked_at is not None
            else None
        ),
        "delivered_at": (
            room.delivered_at.isoformat() if room.delivered_at is not None else None
        ),
        "completed_at": (
            room.completed_at.isoformat() if room.completed_at is not None else None
        ),
        "messages": room.messages or [],
    }
