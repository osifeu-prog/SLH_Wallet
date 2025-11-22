import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

logger = logging.getLogger("slh_wallet.trade_router")

router = APIRouter(prefix="/api/trade", tags=["trade"])


@router.get("/offers", response_model=List[schemas.TradeOfferOut])
def list_offers(db: Session = Depends(get_db)):
    stmt = select(models.TradeOffer).where(models.TradeOffer.is_active.is_(True))
    offers = db.execute(stmt).scalars().all()
    return offers


@router.post("/create-offer", response_model=schemas.TradeOfferOut)
def create_offer(
    payload: schemas.TradeOfferCreate,
    db: Session = Depends(get_db),
):
    # ✅ ולידציה נוספת - בדיקה שהמשתמש קיים
    wallet = db.get(models.Wallet, payload.telegram_id)
    if not wallet:
        raise HTTPException(
            status_code=400, 
            detail="Wallet not found. Please register first."
        )

    # ✅ ולידציה עסקית - הגבלת כמות
    if payload.amount > 10000:
        raise HTTPException(
            status_code=400,
            detail="Amount too large. Maximum allowed: 10,000"
        )

    offer = models.TradeOffer(
        telegram_id=payload.telegram_id,
        token_symbol=payload.token_symbol,
        amount=payload.amount,
        price_bnb=payload.price_bnb,
        is_active=True,
    )
    
    db.add(offer)
    db.commit()
    db.refresh(offer)
    return offer


@router.delete("/offer/{offer_id}")
def cancel_offer(
    offer_id: int,
    telegram_id: str,
    db: Session = Depends(get_db),
):
    offer = db.get(models.TradeOffer, offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    
    if offer.telegram_id != telegram_id:
        raise HTTPException(status_code=403, detail="Not authorized to cancel this offer")
    
    offer.is_active = False
    db.commit()
    
    return {"status": "cancelled", "offer_id": offer_id}
