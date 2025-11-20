
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    telegram_id: str
    username: Optional[str] = None
    first_name: Optional[str] = None

class UserOut(UserBase):
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True

class WalletRegisterIn(BaseModel):
    telegram_id: str
    username: Optional[str] = None
    first_name: Optional[str] = None
    bnb_address: Optional[str] = None
    slh_address: Optional[str] = None

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

class TradeOfferCreate(BaseModel):
    telegram_id: str
    amount: float
    price_per_token: float
    token_symbol: str = "SLH"

class TradeOfferOut(BaseModel):
    id: int
    seller_username: Optional[str]
    token_symbol: str
    amount: float
    price_per_token: float
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
