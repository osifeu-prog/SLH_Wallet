
from __future__ import annotations

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models, schemas

logger = logging.getLogger("slh_wallet.trade_router")

router = APIRouter(tags=["trade"])


@router.get("/api/trade/offers", response_model=list[schemas.TradeOfferOut])
def list_offers(
    db: Session = Depends(get_db),
    status: str = Query("ACTIVE"),
    limit: int = Query(50, ge=1, le=200),
):
    stmt = (
        select(models.TradeOffer)
        .where(models.TradeOffer.status == status)
        .order_by(models.TradeOffer.created_at.desc())
        .limit(limit)
    )
    offers = db.scalars(stmt).all()
    return offers


@router.post("/api/trade/create-offer", response_model=schemas.TradeOfferOut)
def create_offer(
    telegram_id: str = Query(..., alias="telegram_id"),
    token_symbol: str = Query("SLH", alias="token_symbol"),
    amount: float = Query(..., gt=0),
    price_bnb: float = Query(..., gt=0),
    db: Session = Depends(get_db),
):
    # Basic check – seller must have wallet
    wallet = db.get(models.Wallet, telegram_id)
    if not wallet:
        raise HTTPException(status_code=400, detail="Wallet not found for this telegram_id")

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
