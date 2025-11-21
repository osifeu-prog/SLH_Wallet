from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String

from .database import Base


class Wallet(Base):
    __tablename__ = "wallets"

    telegram_id = Column(String, primary_key=True, index=True)
    username = Column(String, nullable=True, index=True)
    first_name = Column(String, nullable=True)

    bnb_address = Column(String, nullable=True)
    slh_address = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TradeOffer(Base):
    __tablename__ = "trade_offers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    telegram_id = Column(String, index=True)
    token_symbol = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    price_bnb = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
