import os
import secrets
from datetime import datetime
from typing import List

from database.db import get_db, get_session
from database.models import Room
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from utils.logging_config import get_logger

from .utils.utils import room_to_dict

logger = get_logger()
router = APIRouter()


class RoomCreate(BaseModel):
    seller_id: str
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


@router.post("/rooms/create")
def create_room(room_data: RoomCreate, db: Session = Depends(get_db)):
    """Seller creates a room"""
    room_phrase = generate_room_phrase()

    room = Room(
        room_phrase=room_phrase,
        seller_id=room_data.seller_id,
        amount=room_data.amount,
        status="WAITING_FOR_BUYER",
        created_at=datetime.now(),
    )
    db.add(room)
    return {"success": True, "room": room_to_dict(room)}
