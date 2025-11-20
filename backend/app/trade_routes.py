
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .db import get_db
from . import models, schemas
from .logger import logger

router = APIRouter(prefix="/api/trade", tags=["Trading"])

@router.get("/offers", response_model=List[schemas.TradeOfferOut])
def list_offers(db: Session = Depends(get_db)):
    offers = db.query(models.TradeOffer).filter(models.TradeOffer.is_active == True).order_by(models.TradeOffer.created_at.desc()).all()
    result = []
    for o in offers:
        result.append(
            schemas.TradeOfferOut(
                id=o.id,
                seller_username=o.seller.username if o.seller else None,
                token_symbol=o.token_symbol,
                amount=o.amount,
                price_per_token=o.price_per_token,
                is_active=o.is_active,
                created_at=o.created_at,
            )
        )
    return result

@router.post("/create-offer", response_model=schemas.TradeOfferOut)
def create_offer(payload: schemas.TradeOfferCreate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.telegram_id == payload.telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found – register wallet first")
    offer = models.TradeOffer(
        seller=user,
        token_symbol=payload.token_symbol,
        amount=payload.amount,
        price_per_token=payload.price_per_token,
    )
    db.add(offer)
    db.commit()
    db.refresh(offer)
    logger.info(f"[TRADE] New offer id={offer.id} by telegram_id={payload.telegram_id}")
    return schemas.TradeOfferOut(
        id=offer.id,
        seller_username=user.username,
        token_symbol=offer.token_symbol,
        amount=offer.amount,
        price_per_token=offer.price_per_token,
        is_active=offer.is_active,
        created_at=offer.created_at,
    )
