from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Float, String
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    role = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now())


class Wallet(Base):
    __tablename__ = "wallets"

    user_id = Column(String, primary_key=True)
    balance = Column(Float, default=0.0)
    locked = Column(Float, default=0.0)
    transactions = Column(JSON, default=list)


class Room(Base):
    __tablename__ = "rooms"

    room_phrase = Column(String, primary_key=True)
    seller_id = Column(String, nullable=False)
    buyer_id = Column(String, nullable=True)
    amount = Column(Float, nullable=False)
    description = Column(String, nullable=False)
    required_evidence = Column(JSON)
    status = Column(String, default="WAITING_FOR_BUYER")

    # Transaction Details
    transaction_id = Column(String, nullable=True)
    escrow_address = Column(String, nullable=True)
    commitment_hash = Column(String, nullable=True)

    # Cryptographic shares
    shares = Column(JSON)

    # Evidence
    evidence_submitted = Column(JSON)
    ai_verification_result = Column(JSON, nullable=True)

    # Timeline
    created_at = Column(DateTime, default=datetime.now())
    buyer_joined_at = Column(DateTime, nullable=True)
    funds_locked_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Messages
    messages = Column(JSON, default=list)


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True)
    room_phrase = Column(String, nullable=False)
    buyer_id = Column(String, nullable=False)
    seller_id = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    master_secret = Column(String, nullable=False)  # TODO: Need to encrypt this
