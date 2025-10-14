from database.db import get_db
from database.models import User, Wallet
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from utils.logging_config import get_logger

logger = get_logger("routes.wallet")
router = APIRouter()


@router.get("/wallet/{user_id}")
def get_wallet(user_id: str, db: Session = Depends(get_db)):
    """Get wallet information for a user with comprehensive error handling and logging"""
    logger.info(f"Wallet request for user: {user_id}")
    
    try:
        # Validate input
        if not user_id or not user_id.strip():
            logger.warning("Empty user_id provided for wallet request")
            raise HTTPException(status_code=400, detail="User ID cannot be empty")

        # Check if user exists
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            logger.warning(f"User not found for wallet request: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")

        # Get or create wallet
        wallet = db.query(Wallet).filter_by(user_id=user_id).first()
        if not wallet:
            logger.info(f"Creating new wallet for user: {user_id} (role: {user.role})")
            # Create wallet if it doesn't exist
            initial_balance = 1000 if user.role == "BUYER" else 500
            wallet = Wallet(
                user_id=user_id, balance=initial_balance, locked=0.0, transactions=[]
            )
            db.add(wallet)
            db.commit()
            db.refresh(wallet)
            logger.info(f"Wallet created for user {user_id} with balance: {initial_balance}")
        else:
            logger.debug(f"Wallet found for user {user_id}: balance={wallet.balance}, locked={wallet.locked}")

        response_data = {
            "user_id": wallet.user_id,
            "balance": wallet.balance,
            "locked": wallet.locked,
            "transactions": wallet.transactions or [],
        }
        
        logger.info(f"Wallet data retrieved successfully for user: {user_id}")
        return response_data

    except HTTPException:
        # Re-raise HTTP exceptions as they are expected
        raise
    except Exception as e:
        logger.error(f"Unexpected error retrieving wallet for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while retrieving wallet")
