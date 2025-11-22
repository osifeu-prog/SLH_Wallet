from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String
from .database import Base


class Wallet(Base):
    __tablename__ = "wallets"

    telegram_id = Column(String(50), primary_key=True, index=True)
    username = Column(String(50), nullable=True, index=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)

    bnb_address = Column(String(255), nullable=True)
    slh_address = Column(String(255), nullable=True)
    slh_ton_address = Column(String(255), nullable=True)

    bank_account_number = Column(String(100), nullable=True)
    bank_account_name = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TradeOffer(Base):
    __tablename__ = "trade_offers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    seller_telegram_id = Column(String(50), index=True, nullable=False)
    buyer_telegram_id = Column(String(50), index=True, nullable=True)

    token_symbol = Column(String(50), nullable=False)
    amount = Column(Float, nullable=False)
    price_bnb = Column(Float, nullable=False)

    status = Column(String(20), default="ACTIVE", index=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Referral(Base):
    __tablename__ = "referrals"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    referrer_telegram_id = Column(String(50), index=True, nullable=False)
    referred_telegram_id = Column(String(50), index=True, nullable=False, unique=True)
    reward_amount_slh_ton = Column(Float, default=0.001)

    created_at = Column(DateTime, default=datetime.utcnow)
