from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models, schemas

router = APIRouter(prefix="/api/trade", tags=["trade"])


@router.get("/offers", response_model=List[schemas.TradeOfferPublic])
def list_offers(db: Session = Depends(get_db)):
    stmt = (
        select(models.TradeOffer)
        .where(models.TradeOffer.status == "ACTIVE")
        .order_by(models.TradeOffer.created_at.desc())
        .limit(50)
    )
    offers = db.execute(stmt).scalars().all()
    return [
        schemas.TradeOfferPublic(
            id=o.id,
            seller_telegram_id=o.seller_telegram_id,
            token_symbol=o.token_symbol,
            amount=o.amount,
            price_bnb=o.price_bnb,
            status=o.status,
            created_at=o.created_at,
        )
        for o in offers
    ]


@router.post("/create-offer", response_model=schemas.TradeOfferOut)
def create_offer(
    telegram_id: str,
    token_symbol: str,
    amount: float,
    price_bnb: float,
    db: Session = Depends(get_db),
):
    offer = models.TradeOffer(
        seller_telegram_id=telegram_id,
        token_symbol=token_symbol,
        amount=amount,
        price_bnb=price_bnb,
        status="ACTIVE",
    )
    db.add(offer)
    db.commit()
    db.refresh(offer)
    return offer


@router.get("/summary", response_model=schemas.MarketSummary)
def market_summary(db: Session = Depends(get_db)):
    total = db.query(models.TradeOffer).filter(models.TradeOffer.status == "ACTIVE").count()
    rows = (
        db.query(
            models.TradeOffer.token_symbol,
            func.avg(models.TradeOffer.price_bnb),
        )
        .filter(models.TradeOffer.status == "ACTIVE")
        .group_by(models.TradeOffer.token_symbol)
        .all()
    )
    tokens = [r[0] for r in rows]
    avg_price_by_token = {r[0]: float(r[1]) for r in rows}

    return schemas.MarketSummary(
        active_offers=total,
        tokens=tokens,
        avg_price_by_token=avg_price_by_token,
    )
