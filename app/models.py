
from __future__ import annotations

import datetime as dt
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .database import Base


class Wallet(Base):
    __tablename__ = "wallets"

    telegram_id: str = Column(String(64), primary_key=True, index=True)
    username: Optional[str] = Column(String(64), index=True, nullable=True)
    first_name: Optional[str] = Column(String(128), nullable=True)
    last_name: Optional[str] = Column(String(128), nullable=True)

    # External chain addresses
    bnb_address: Optional[str] = Column(String(255), nullable=True)
    slh_address: Optional[str] = Column(String(255), nullable=True)
    slh_ton_address: Optional[str] = Column(String(255), nullable=True)

    # Optional bank details for fiat payments
    bank_account_name: Optional[str] = Column(String(255), nullable=True)
    bank_account_number: Optional[str] = Column(String(64), nullable=True)

    # Internal SLH ledger
    internal_slh_balance: float = Column(Float, nullable=False, default=0.0)
    internal_slh_locked: float = Column(Float, nullable=False, default=0.0)

    created_at = Column(DateTime(timezone=True), default=dt.datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        default=dt.datetime.utcnow,
        onupdate=dt.datetime.utcnow,
    )

    trade_offers = relationship("TradeOffer", back_populates="seller", lazy="selectin")


class TradeOffer(Base):
    __tablename__ = "trade_offers"

    id: int = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Links to wallet (by telegram)
    seller_telegram_id: str = Column(
        String(64), ForeignKey("wallets.telegram_id"), nullable=False, index=True
    )
    buyer_telegram_id: Optional[str] = Column(String(64), nullable=True, index=True)

    token_symbol: str = Column(String(32), nullable=False, default="SLH")
    amount: float = Column(Float, nullable=False)
    price_bnb: float = Column(Float, nullable=False)

    status: str = Column(
        String(32),
        nullable=False,
        default="ACTIVE",  # ACTIVE, COMPLETED, CANCELLED
        index=True,
    )

    created_at = Column(DateTime(timezone=True), default=dt.datetime.utcnow, index=True)
    updated_at = Column(
        DateTime(timezone=True),
        default=dt.datetime.utcnow,
        onupdate=dt.datetime.utcnow,
    )

    seller = relationship("Wallet", back_populates="trade_offers", lazy="joined")


class InternalTransfer(Base):
    __tablename__ = "internal_transfers"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    from_telegram_id: str = Column(String(64), index=True)
    to_telegram_id: str = Column(String(64), index=True)
    amount: float = Column(Float, nullable=False)
    memo: Optional[str] = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), default=dt.datetime.utcnow, index=True)


class StakingPosition(Base):
    __tablename__ = "staking_positions"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id: str = Column(String(64), index=True)
    amount_locked: float = Column(Float, nullable=False)
    annual_rate_percent: float = Column(Float, nullable=False, default=120.0)
    # we can compute monthly 10% later from annual if needed

    started_at = Column(DateTime(timezone=True), default=dt.datetime.utcnow)
    unlock_at = Column(DateTime(timezone=True), nullable=True)

    is_active: bool = Column(Boolean, nullable=False, default=True)
