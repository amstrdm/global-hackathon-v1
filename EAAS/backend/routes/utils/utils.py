import hashlib
import secrets

from database.models import Room


def room_to_dict(room: Room) -> dict:
    """Convert Room model to dict"""
    return {
        "room_code": room.room_phrase,
        "seller_id": room.seller_id,
        "buyer_id": room.buyer_id,
        "seller_public_key": str(room.seller_public_key),
        "buyer_public_key": str(room.buyer_public_key),
        "ai_public_key": str(room.ai_public_key),
        "amount": room.amount,
        "description": room.description,
        "required_evidence": room.required_evidence,
        "status": room.status,
        "transaction_id": room.transaction_id,
        "escrow_address": room.escrow_address,
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


def keccak256_with_stdlib() -> str:
    """
    WARNING: This uses hashlib.sha3_256 (NIST SHA3-256), NOT Keccak-256.
    The result is therefore NOT the correct Keccak-256 used by EIP-55.
    This function exists only for a zero-dependency fallback (not EIP-55 correct).
    """
    addr = secrets.token_hex(20)  # 40 hex chars
    addr = addr.lower()

    h = hashlib.sha3_256()
    h.update(addr.encode("ascii"))
    hash_hex = h.hexdigest()

    checksum_addr = "".join(
        ch.upper() if int(hash_hex[i], 16) >= 8 else ch for i, ch in enumerate(addr)
    )
    # Note: THIS IS NOT EIP-55 (because sha3_256 != keccak_256), but it is deterministic and looks like checksumed.
    return "0x" + checksum_addr
