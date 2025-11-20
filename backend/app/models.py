
from sqlalchemy import Column, String, Integer, DateTime, Float, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, index=True)
    first_name = Column(String, index=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    wallet = relationship("Wallet", back_populates="owner", uselist=False)

class Wallet(Base):
    __tablename__ = "wallets"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    bnb_address = Column(String, index=True)
    slh_address = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="wallet")

class TradeOffer(Base):
    __tablename__ = "trade_offers"
    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey("users.id"))
    token_symbol = Column(String, default="SLH")
    amount = Column(Float, nullable=False)
    price_per_token = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    seller = relationship("User")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    from_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    to_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    token_symbol = Column(String, default="SLH")
    amount = Column(Float, nullable=False)
    tx_hash = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    note = Column(Text, nullable=True)
