
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


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
        orm_mode = True


class TradeOfferOut(BaseModel):
    id: int
    token_symbol: str
    amount: float
    price_bnb: float
    is_active: bool
    created_at: datetime

    class Config:
        orm_mode = True
