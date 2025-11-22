
from __future__ import annotations

import datetime as dt
from typing import Optional

from pydantic import BaseModel, Field


class WalletBase(BaseModel):
    telegram_id: str
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class WalletRegisterIn(WalletBase):
    bnb_address: Optional[str] = None
    slh_address: Optional[str] = None
    slh_ton_address: Optional[str] = None
    bank_account_name: Optional[str] = None
    bank_account_number: Optional[str] = None


class WalletOut(WalletBase):
    bnb_address: Optional[str] = None
    slh_address: Optional[str] = None
    slh_ton_address: Optional[str] = None
    bank_account_name: Optional[str] = None
    bank_account_number: Optional[str] = None

    internal_slh_balance: float = 0.0
    internal_slh_locked: float = 0.0

    created_at: Optional[dt.datetime] = None
    updated_at: Optional[dt.datetime] = None

    class Config:
        from_attributes = True


class WalletBalancesOut(BaseModel):
    success: bool = True
    bnb_address: Optional[str] = None
    slh_address: Optional[str] = None
    slh_ton_address: Optional[str] = None
    internal_slh_balance: float = 0.0
    internal_slh_locked: float = 0.0

    bnb_balance: float = 0.0
    slh_balance_onchain: float = 0.0
    slh_balance_total: float = 0.0


class TradeOfferCreate(BaseModel):
    telegram_id: str
    token_symbol: str = Field(default="SLH")
    amount: float
    price_bnb: float


class TradeOfferOut(BaseModel):
    id: int
    seller_telegram_id: str
    buyer_telegram_id: Optional[str] = None
    token_symbol: str
    amount: float
    price_bnb: float
    status: str
    created_at: dt.datetime

    class Config:
        from_attributes = True
