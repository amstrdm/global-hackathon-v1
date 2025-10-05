from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Float, String
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    role = Column(String, nullable=False)
    public_key = Column(String, nullable=False)
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
    description = Column(String, nullable=True)
    status = Column(String, default="WAITING_FOR_BUYER")

    # Transaction Details
    transaction_id = Column(String, nullable=True)
    escrow_address = Column(String, nullable=True)
    buyer_public_key = Column(String, nullable=True)
    seller_public_key = Column(String, nullable=True)
    ai_public_key = Column(String, nullable=True)
    private_key = Column(String, nullable=True)
    # Cryptographic shares
    contract = Column(JSON, nullable=True)

    # AI Dispute System
    dispute_status = Column(
        String, nullable=True
    )  # e.g., AWAITING_EVIDENCE, IN_REVIEW, RESOLVED
    required_evidence = Column(
        JSON, nullable=True
    )  # Stores the list of what the AI needs
    submitted_evidence = Column(
        JSON, nullable=True, default=lambda: {}
    )  # Stores links/filenames of submitted evidence
    ai_verdict = Column(JSON, nullable=True)  # Stores the final JSON output from the AI

    # Timeline
    created_at = Column(DateTime, default=datetime.now())
    buyer_joined_at = Column(DateTime, nullable=True)
    funds_locked_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Messages
    messages = Column(MutableList.as_mutable(JSON), default=list)


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True)
    room_phrase = Column(String, nullable=False)
    buyer_id = Column(String, nullable=False)
    seller_id = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    master_secret = Column(String, nullable=False)  # TODO: Need to encrypt this
