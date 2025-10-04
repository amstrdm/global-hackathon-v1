import uuid

from database.db import get_db
from database.models import User, Wallet
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

router = APIRouter()


class UserCreate(BaseModel):
    username: str
    role: str = "BUYER"


@router.post("/register")
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):

    if db.query(User).filter_by(username=user_data.username).first():
        raise HTTPException(status_code=409, detail="Username already taken.")

    user_id = str(uuid.uuid4())

    user = User(
        id=user_id, username=user_data.username.lower(), role=user_data.role.upper()
    )
    db.add(user)

    # Create Wallet
    initial_balance = 1000 if user_data.role.upper() == "BUYER" else 500
    wallet = Wallet(
        user_id=user_id, balance=initial_balance, locked=0.0, transactions=[]
    )
    db.add(wallet)

    return {
        "user_id": user_id,
        "username": user_data.username,
        "role": user_data.role,
        "balance": initial_balance,
    }
