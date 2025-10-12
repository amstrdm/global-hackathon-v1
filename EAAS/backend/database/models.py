from datetime import datetime
from typing import Any, List, Optional

from sqlalchemy import JSON
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    role: Mapped[str]
    public_key: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)


class Wallet(Base):
    __tablename__ = "wallets"

    user_id: Mapped[str] = mapped_column(primary_key=True)
    balance: Mapped[float] = mapped_column(default=0.0)
    locked: Mapped[float] = mapped_column(default=0.0)
    transactions: Mapped[List[dict[str, Any]]] = mapped_column(JSON, default=list)


class Room(Base):
    __tablename__ = "rooms"

    room_phrase: Mapped[str] = mapped_column(primary_key=True)
    seller_id: Mapped[str]
    buyer_id: Mapped[Optional[str]]
    amount: Mapped[float]
    description: Mapped[Optional[str]]
    status: Mapped[Optional[str]] = mapped_column(default="WAITING_FOR_BUYER")

    # Transaction Details
    transaction_id: Mapped[Optional[str]]
    escrow_address: Mapped[Optional[str]]
    buyer_public_key: Mapped[Optional[str]]
    seller_public_key: Mapped[Optional[str]]
    ai_public_key: Mapped[Optional[str]]
    private_key: Mapped[Optional[str]]
    # Cryptographic shares
    contract: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)

    # AI Dispute System
    dispute_status: Mapped[Optional[str]]
    required_evidence: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)
    submitted_evidence: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON, default=lambda: {}
    )  # Stores links/filenames of submitted evidence
    ai_verdict: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)  # Timeline
    created_at: Mapped[Optional[datetime]] = mapped_column(default=datetime.now)
    buyer_joined_at: Mapped[Optional[datetime]]
    funds_locked_at: Mapped[Optional[datetime]]
    delivered_at: Mapped[Optional[datetime]]
    completed_at: Mapped[Optional[datetime]]

    # Messages
    messages: Mapped[List[dict[str, Any]]] = mapped_column(
        MutableList.as_mutable(JSON), default=list
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(primary_key=True)
    room_phrase: Mapped[str]
    buyer_id: Mapped[str]
    seller_id: Mapped[str]
    amount: Mapped[float]
    master_secret: Mapped[str]  # TODO: Need to encrypt this
