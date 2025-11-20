
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, index=True, nullable=True)
    first_name = Column(String, nullable=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    wallets = relationship("Wallet", back_populates="user")


class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    bnb_address = Column(String, index=True, nullable=True)
    slh_address = Column(String, index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="wallets")


class TradeOffer(Base):
    __tablename__ = "trade_offers"

    id = Column(Integer, primary_key=True, index=True)
    maker_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token_symbol = Column(String, default="SLH")
    amount = Column(Numeric(38, 8), nullable=False)
    price_bnb = Column(Numeric(38, 8), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    maker = relationship("User")


class TransactionLog(Base):
    __tablename__ = "tx_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    kind = Column(String, nullable=False)  # 'wallet_register', 'trade', 'bot', 'web'
    description = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
