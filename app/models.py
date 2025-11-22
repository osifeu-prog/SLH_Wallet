from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String
from .database import Base


def utcnow():
    return datetime.utcnow()


class Wallet(Base):
    __tablename__ = "wallets"

    telegram_id = Column(String, primary_key=True, index=True)
    username = Column(String, nullable=True, index=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)

    # External blockchain addresses
    bnb_address = Column(String, nullable=True)
    slh_address = Column(String, nullable=True)          # SLH on BNB chain
    slh_ton_address = Column(String, nullable=True)      # SLH on TON chain (future)

    # Optional bank info for off-chain settlements
    bank_account_number = Column(String, nullable=True)
    bank_account_name = Column(String, nullable=True)

    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class InternalBalance(Base):
    """
    Simple internal ledger for the community (P2P / rewards / games).
    asset examples: 'SLH_BNB', 'SLH_TON', 'SLH_INTERNAL'
    """

    __tablename__ = "internal_balances"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    telegram_id = Column(String, index=True, nullable=False)
    asset = Column(String, nullable=False)
    amount = Column(Float, nullable=False, default=0.0)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class TradeOffer(Base):
    __tablename__ = "trade_offers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    seller_telegram_id = Column(String, index=True, nullable=False)
    buyer_telegram_id = Column(String, index=True, nullable=True)

    token_symbol = Column(String, nullable=False)  # e.g. 'SLH_BNB' or 'SLH_TON'
    amount = Column(Float, nullable=False)
    price_bnb = Column(Float, nullable=False)      # price per unit in BNB

    status = Column(String, nullable=False, default="ACTIVE")  # ACTIVE / PENDING_PAYMENT / COMPLETED / CANCELLED

    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
