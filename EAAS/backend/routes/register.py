import uuid

from database.db import get_db
from database.models import User, Wallet
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from utils.logging_config import get_logger

logger = get_logger("routes.register")
router = APIRouter()


class UserCreate(BaseModel):
    username: str
    role: str = "BUYER"
    public_key: str


@router.post("/register")
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user with proper error handling and logging"""
    logger.info(f"Registration attempt for username: {user_data.username}, role: {user_data.role}")
    
    try:
        # Validate input
        if not user_data.username or not user_data.username.strip():
            logger.warning("Registration attempt with empty username")
            raise HTTPException(status_code=400, detail="Username cannot be empty")
        
        if user_data.role.upper() not in ["BUYER", "SELLER"]:
            logger.warning(f"Invalid role provided: {user_data.role}")
            raise HTTPException(status_code=400, detail="Role must be either BUYER or SELLER")
        
        if not user_data.public_key or not user_data.public_key.strip():
            logger.warning("Registration attempt with empty public key")
            raise HTTPException(status_code=400, detail="Public key cannot be empty")

        # Check if username already exists
        existing_user = db.query(User).filter_by(username=user_data.username.lower()).first()
        if existing_user:
            logger.warning(f"Registration attempt with existing username: {user_data.username}")
            raise HTTPException(status_code=409, detail="Username already taken.")

        user_id = str(uuid.uuid4())
        logger.debug(f"Generated user ID: {user_id}")

        # Create user
        user = User(
            id=user_id,
            username=user_data.username.lower(),
            role=user_data.role.upper(),
            public_key=user_data.public_key,
        )
        db.add(user)
        logger.debug(f"User created: {user.username}")

        # Create wallet with initial balance
        initial_balance = 1000 if user_data.role.upper() == "BUYER" else 500
        wallet = Wallet(
            user_id=user_id, balance=initial_balance, locked=0.0, transactions=[]
        )
        db.add(wallet)
        logger.debug(f"Wallet created for user {user_id} with balance: {initial_balance}")

        response_data = {
            "user_id": user_id,
            "username": user_data.username,
            "role": user_data.role,
            "balance": initial_balance,
        }
        
        logger.info(f"User registration successful: {user_data.username} ({user_data.role})")
        return response_data

    except HTTPException:
        # Re-raise HTTP exceptions as they are expected
        raise
    except Exception as e:
        logger.error(f"Unexpected error during user registration: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during registration")
