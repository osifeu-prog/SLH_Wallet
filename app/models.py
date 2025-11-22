from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String
from .database import Base


class Wallet(Base):
    __tablename__ = "wallets"

    telegram_id = Column(String, primary_key=True, index=True)
    username = Column(String, nullable=True, index=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)  # ✅ שם משפחה חדש

    bnb_address = Column(String, nullable=True)
    slh_address = Column(String, nullable=True)
    slh_ton_address = Column(String, nullable=True)  # ✅ TON wallet address for SLH on TON
    
    # ✅ פרטי בנק חדשים
    bank_account_number = Column(String, nullable=True)
    bank_name = Column(String, nullable=True)
    bank_branch = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TradeOffer(Base):
    __tablename__ = "trade_offers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # מי שמפרסם את ההצעה בפועל (owner)
    seller_telegram_id = Column(String, index=True, nullable=True)

    # ממולא כאשר יש קונה שסגר עסקה
    buyer_telegram_id = Column(String, index=True, nullable=True)

    # תאימות לאחור – חלק מהקוד הישן עדיין משתמש בשדה telegram_id
    telegram_id = Column(String, index=True, nullable=True)

    token_symbol = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    price_bnb = Column(Float, nullable=False)

    # סטטוס לוגי של העסקה (ACTIVE / COMPLETED / CANCELLED)
    status = Column(String, nullable=False, default="ACTIVE")

    # דגל ישן – נשמר כדי לא לשבור קוד ישן
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
