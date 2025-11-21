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
    """
    מחזיר את כל ההצעות הפעילות, ממוינות לפי זמן יצירה (מהחדש לישן).
    """
    stmt = (
        select(models.TradeOffer)
        .where(models.TradeOffer.is_active.is_(True))
        .order_by(models.TradeOffer.created_at.desc())
    )
    offers = db.execute(stmt).scalars().all()
    return [schemas.TradeOfferOut.from_orm(o) for o in offers]


@router.post("/create-offer", response_model=schemas.TradeOfferOut)
def create_offer(
    telegram_id: str,
    token_symbol: str,
    amount: float,
    price_bnb: float,
    db: Session = Depends(get_db),
):
    """
    יצירת הצעת מסחר חדשה.
    נקרא כיום מה-Swagger עם פרמטרים ב-query.
    """
    if not telegram_id or len(telegram_id) > 50:
        raise HTTPException(status_code=400, detail="Invalid telegram ID")

    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    if price_bnb <= 0:
        raise HTTPException(status_code=400, detail="Price must be positive")

    payload = schemas.TradeOfferCreate(
        telegram_id=telegram_id,
        token_symbol=token_symbol,
        amount=amount,
        price_bnb=price_bnb,
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

    logger.info(
        "Created trade offer id=%s by telegram_id=%s %s amount=%s price_bnb=%s",
        offer.id,
        offer.telegram_id,
        offer.token_symbol,
        offer.amount,
        offer.price_bnb,
    )

    return schemas.TradeOfferOut.from_orm(offer)


@router.post("/offers/{offer_id}/cancel")
def cancel_offer(
    offer_id: int,
    telegram_id: str,
    db: Session = Depends(get_db),
):
    """
    ביטול הצעה – רק מי שיצר את ההצעה יכול לבטל.
    """
    offer = db.get(models.TradeOffer, offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")

    if offer.telegram_id != telegram_id:
        raise HTTPException(status_code=403, detail="Not authorized to cancel this offer")

    offer.is_active = False
    db.commit()

    logger.info("Cancelled trade offer id=%s by telegram_id=%s", offer_id, telegram_id)

    return {"status": "cancelled", "offer_id": offer_id}
