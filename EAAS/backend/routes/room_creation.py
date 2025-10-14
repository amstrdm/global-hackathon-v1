import os
import secrets
from datetime import datetime
from typing import List

from database.db import get_db, get_session
from database.models import Room, User
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from utils.logging_config import get_logger

from .utils.smart_contract import CryptoUtils
from .utils.utils import keccak256_with_stdlib, room_to_dict

logger = get_logger()
router = APIRouter()

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
env_path = os.path.join(project_root, ".env")
load_dotenv(env_path)


class RoomCreate(BaseModel):
    amount: float


def generate_room_phrase(num_words=4):
    """
    Generates a secure, random seed phrase from a word list.

    Args:
        num_words (int): The number of words in the phrase (e.g., 3, 4, or 5).

    Returns:
        str: The generated phrase as a space-separated string.
    """

    try:
        bip39path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "utils", "bip39.txt"
        )
        with open(bip39path, "r") as f:
            wordlist = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        logger.error("'bip39.txt' not found.")
        raise

    if len(wordlist) != 2048:
        logger.error(f"Word List has {len(wordlist)} words, expected 2048")
        raise

    while True:
        phrase = " ".join([secrets.choice(wordlist) for _ in range(num_words)])

        with get_session() as db:
            existing_phrase = db.query(Room).filter_by(room_phrase=phrase).first()
            if not existing_phrase:
                return phrase


@router.post("/rooms/create/{user_id}")
def create_room(room_data: RoomCreate, user_id: str, db: Session = Depends(get_db)):
    """Seller creates a room"""
    user = db.query(User).filter_by(id=user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User does not exist.")

    if user.role != "SELLER":
        raise HTTPException(
            status_code=403, detail="You need to be a Seller to create a room."
        )

    ai_public_key_pem = os.getenv("AI_PUBLIC_KEY")
    if not ai_public_key_pem:
        raise HTTPException(
            status_code=500,
            detail="AI Oracle public key is not configured on the server.",
        )

    room_phrase = generate_room_phrase()
    escrow_address = keccak256_with_stdlib()

    room = Room(
        room_phrase=room_phrase,
        escrow_address=escrow_address,
        seller_id=user.id,
        seller_public_key=user.public_key,
        ai_public_key=ai_public_key_pem,
        amount=room_data.amount,
        status="WAITING_FOR_BUYER",
        created_at=datetime.now(),
    )
    db.add(room)
    return {"success": True, "room": room_to_dict(room)}
