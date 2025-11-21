from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator


class WalletRegisterIn(BaseModel):
    telegram_id: str = Field(..., description="Telegram user id", min_length=1, max_length=50)
    username: Optional[str] = Field(None, max_length=100)
    first_name: Optional[str] = Field(None, max_length=100)
    bnb_address: Optional[str] = Field(None, max_length=200)
    slh_address: Optional[str] = Field(None, max_length=200)

    @validator('bnb_address', 'slh_address')
    def validate_address(cls, v):
        if v is not None and len(v.strip()) == 0:
            return None
        return v


class WalletOut(BaseModel):
    telegram_id: str
    username: Optional[str] = None
    first_name: Optional[str] = None
    bnb_address: Optional[str] = None
    slh_address: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TradeOfferOut(BaseModel):
    id: int
    telegram_id: str
    token_symbol: str
    amount: float
    price_bnb: float
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ✅ schema חדש עם ולידציה ליצירת הצעות trade
class TradeOfferCreate(BaseModel):
    telegram_id: str = Field(..., min_length=1, max_length=50)
    token_symbol: str = Field(..., regex="^(BNB|SLH)$")
    amount: float = Field(..., gt=0, description="Must be positive")
    price_bnb: float = Field(..., gt=0, description="Must be positive")

    @validator('amount', 'price_bnb')
    def validate_positive(cls, v):
        if v <= 0:
            raise ValueError('Must be positive')
        return v
