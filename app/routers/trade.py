from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/trade", tags=["trade"])


@router.get("/offers", response_model=List[schemas.TradeOfferOut])
def list_offers(db: Session = Depends(get_db)):
    stmt = select(models.TradeOffer).where(models.TradeOffer.is_active.is_(True))
    offers = db.execute(stmt).scalars().all()
    return offers


@router.post("/create-offer", response_model=schemas.TradeOfferOut)
def create_offer(
    telegram_id: str,
    token_symbol: str,
    amount: float,
    price_bnb: float,
    db: Session = Depends(get_db),
):
    offer = models.TradeOffer(
        telegram_id=telegram_id,
        token_symbol=token_symbol,
        amount=amount,
        price_bnb=price_bnb,
        is_active=True,
    )
    db.add(offer)
    db.commit()
    db.refresh(offer)
    return offer
