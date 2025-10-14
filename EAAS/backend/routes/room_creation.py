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

logger = get_logger("routes.room_creation")
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
    logger.debug(f"Generating room phrase with {num_words} words")

    try:
        bip39path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "utils", "bip39.txt"
        )
        with open(bip39path, "r") as f:
            wordlist = [line.strip() for line in f if line.strip()]
        logger.debug(f"Loaded BIP39 wordlist with {len(wordlist)} words")
    except FileNotFoundError:
        logger.error("'bip39.txt' not found.")
        raise
    except Exception as e:
        logger.error(f"Error loading BIP39 wordlist: {e}")
        raise

    if len(wordlist) != 2048:
        logger.error(f"Word List has {len(wordlist)} words, expected 2048")
        raise ValueError("Invalid BIP39 wordlist")

    attempts = 0
    max_attempts = 100  # Prevent infinite loops
    
    while attempts < max_attempts:
        phrase = " ".join([secrets.choice(wordlist) for _ in range(num_words)])
        attempts += 1
        
        try:
            with get_session() as db:
                existing_phrase = db.query(Room).filter_by(room_phrase=phrase).first()
                if not existing_phrase:
                    logger.debug(f"Generated unique room phrase after {attempts} attempts")
                    return phrase
        except Exception as e:
            logger.error(f"Error checking phrase uniqueness: {e}")
            raise
    
    logger.error(f"Failed to generate unique phrase after {max_attempts} attempts")
    raise RuntimeError("Failed to generate unique room phrase")


@router.post("/rooms/create/{user_id}")
def create_room(room_data: RoomCreate, user_id: str, db: Session = Depends(get_db)):
    """Seller creates a room with comprehensive error handling and logging"""
    logger.info(f"Room creation attempt by user: {user_id}, amount: {room_data.amount}")
    
    try:
        # Validate input
        if not user_id or not user_id.strip():
            logger.warning("Empty user_id provided for room creation")
            raise HTTPException(status_code=400, detail="User ID cannot be empty")
        
        if room_data.amount <= 0:
            logger.warning(f"Invalid amount provided: {room_data.amount}")
            raise HTTPException(status_code=400, detail="Amount must be greater than 0")

        # Check if user exists
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            logger.warning(f"User not found: {user_id}")
            raise HTTPException(status_code=404, detail="User does not exist.")

        # Check if user is a seller
        if user.role != "SELLER":
            logger.warning(f"Non-seller attempted to create room: {user_id} (role: {user.role})")
            raise HTTPException(
                status_code=403, detail="You need to be a Seller to create a room."
            )

        # Check AI public key configuration
        ai_public_key_pem = os.getenv("AI_PUBLIC_KEY")
        if not ai_public_key_pem:
            logger.error("AI_PUBLIC_KEY environment variable not set")
            raise HTTPException(
                status_code=500,
                detail="AI Oracle public key is not configured on the server.",
            )

        # Generate room phrase and escrow address
        logger.debug("Generating room phrase and escrow address")
        room_phrase = generate_room_phrase()
        escrow_address = keccak256_with_stdlib()
        logger.debug(f"Generated room phrase: {room_phrase}")

        # Create room
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
        logger.debug(f"Room created: {room_phrase}")

        response_data = {"success": True, "room": room_to_dict(room)}
        logger.info(f"Room creation successful: {room_phrase} by seller {user.username}")
        return response_data

    except HTTPException:
        # Re-raise HTTP exceptions as they are expected
        raise
    except Exception as e:
        logger.error(f"Unexpected error during room creation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during room creation")
