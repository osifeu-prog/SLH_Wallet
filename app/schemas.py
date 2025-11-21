from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator


# -------- Wallet Schemas --------

class WalletRegisterIn(BaseModel):
    telegram_id: str = Field(..., description="Telegram user id", min_length=1, max_length=50)
    username: Optional[str] = Field(None, max_length=100)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)

    bnb_address: Optional[str] = Field(None, max_length=200)
    slh_address: Optional[str] = Field(None, max_length=200)

    # פרטי בנק
    bank_account_number: Optional[str] = Field(None, max_length=100)
    bank_name: Optional[str] = Field(None, max_length=100)
    bank_branch: Optional[str] = Field(None, max_length=100)
    bank_holder_name: Optional[str] = Field(None, max_length=200)


class WalletOut(BaseModel):
    telegram_id: str
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    bnb_address: Optional[str]
    slh_address: Optional[str]
    bank_account_number: Optional[str]
    bank_name: Optional[str]
    bank_branch: Optional[str]
    bank_holder_name: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class BalanceResponse(BaseModel):
    telegram_id: str
    bnb_balance: float
    slh_balance: float
    bnb_address: str
    slh_address: str
    success: bool = True

    class Config:
        from_attributes = True


# -------- Trade Schemas --------

class TradeOfferBase(BaseModel):
    token_symbol: str = Field(..., max_length=20)
    amount: float = Field(..., gt=0)
    price_bnb: float = Field(..., gt=0)

    @validator("token_symbol")
    def token_symbol_upper(cls, v: str) -> str:
        return v.upper()


class TradeOfferCreate(TradeOfferBase):
    telegram_id: str = Field(..., max_length=50)


class TradeOfferOut(TradeOfferBase):
    id: int
    telegram_id: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
