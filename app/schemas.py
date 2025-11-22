from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator


# -------- Wallet schemas --------

class WalletRegisterIn(BaseModel):
    telegram_id: str = Field(..., description="Telegram user id", min_length=1, max_length=50)
    username: Optional[str] = Field(None, max_length=100)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    bnb_address: Optional[str] = Field(None, max_length=200)
    slh_address: Optional[str] = Field(None, max_length=200)
    slh_ton_address: Optional[str] = Field(None, max_length=200)

    bank_account_number: Optional[str] = Field(None, max_length=100)
    bank_account_name: Optional[str] = Field(None, max_length=200)


class WalletOut(BaseModel):
    telegram_id: str
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    bnb_address: Optional[str]
    slh_address: Optional[str]
    slh_ton_address: Optional[str]
    bank_account_number: Optional[str]
    bank_account_name: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class WalletDetailsResponse(BaseModel):
    wallet: WalletOut
    has_bnb_address: bool
    has_slh_address: bool
    has_slh_ton_address: bool
    has_bank_info: bool
    registration_date: Optional[datetime]


class BalanceResponse(BaseModel):
    telegram_id: str
    bnb_balance: float
    slh_balance: float
    slh_ton_balance: float
    slh_ton_factor: float
    bnb_address: Optional[str]
    slh_address: Optional[str]
    slh_ton_address: Optional[str]
    success: bool = True


# -------- Trade / Market schemas --------

class TradeOfferCreate(BaseModel):
    telegram_id: str = Field(..., description="Seller telegram id")
    token_symbol: str = Field(..., description="Token symbol, e.g. SLH_BNB or SLH_TON")
    amount: float = Field(..., gt=0)
    price_bnb: float = Field(..., gt=0)

    @validator("token_symbol")
    def normalize_symbol(cls, v: str) -> str:
        return v.upper()


class TradeOfferOut(BaseModel):
    id: int
    seller_telegram_id: str
    buyer_telegram_id: Optional[str]
    token_symbol: str
    amount: float
    price_bnb: float
    status: str
    created_at: datetime
    updated_at: datetime

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
