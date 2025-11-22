from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class WalletRegisterIn(BaseModel):
    telegram_id: str
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bnb_address: Optional[str] = None
    slh_address: Optional[str] = None
    slh_ton_address: Optional[str] = None


class WalletOut(BaseModel):
    telegram_id: str
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bnb_address: Optional[str] = None
    slh_address: Optional[str] = None
    slh_ton_address: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WalletDetailsResponse(BaseModel):
    wallet: WalletOut
    has_bnb: bool
    has_slh_bnb: bool
    has_slh_ton: bool


class BalanceResponse(BaseModel):
    telegram_id: str
    bnb_address: Optional[str] = None
    slh_address: Optional[str] = None
    slh_ton_address: Optional[str] = None
    bnb: float
    slh_bnb: float
    slh_ton: float
    slh_ton_factor: float


class TradeOfferCreate(BaseModel):
    token_symbol: str
    amount: float
    price_bnb: float


class TradeOfferOut(BaseModel):
    id: int
    seller_telegram_id: str
    buyer_telegram_id: Optional[str]
    token_symbol: str
    amount: float
    price_bnb: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class TradeOfferPublic(BaseModel):
    id: int
    seller_telegram_id: str
    token_symbol: str
    amount: float
    price_bnb: float
    status: str
    created_at: datetime


class MarketSummary(BaseModel):
    active_offers: int
    tokens: List[str]
    avg_price_by_token: dict


class ReferralOut(BaseModel):
    id: int
    referrer_telegram_id: str
    referred_telegram_id: str
    reward_amount_slh_ton: float
    created_at: datetime

    class Config:
        from_attributes = True


class AdminSummary(BaseModel):
    total_wallets: int
    total_referrals: int
    total_trade_offers: int
    active_trade_offers: int
    last_offers: List[TradeOfferOut]
