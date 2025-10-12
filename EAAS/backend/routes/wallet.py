from database.db import get_db
from database.models import User, Wallet
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/wallet/{user_id}")
def get_wallet(user_id: str, db: Session = Depends(get_db)):
    """Get wallet information for a user"""
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    wallet = db.query(Wallet).filter_by(user_id=user_id).first()
    if not wallet:
        # Create wallet if it doesn't exist
        initial_balance = 1000 if user.role == "BUYER" else 500
        wallet = Wallet(
            user_id=user_id, balance=initial_balance, locked=0.0, transactions=[]
        )
        db.add(wallet)
        db.commit()
        db.refresh(wallet)

    return {
        "user_id": wallet.user_id,
        "balance": wallet.balance,
        "locked": wallet.locked,
        "transactions": wallet.transactions or [],
    }
