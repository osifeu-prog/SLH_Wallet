import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

logger = logging.getLogger("slh_wallet.trade_router")

router = APIRouter(prefix="/api/trade", tags=["trade"])


@router.get("/offers", response_model=List[schemas.TradeOfferOut])
def list_offers(db: Session = Depends(get_db)):
    """
    List all active offers, newest first.
    """
    stmt = (
        select(models.TradeOffer)
        .where(models.TradeOffer.status == "ACTIVE")
        .order_by(models.TradeOffer.created_at.desc())
    )
    offers = db.execute(stmt).scalars().all()
    return offers


@router.post("/create-offer", response_model=schemas.TradeOfferOut)
def create_offer(
    payload: schemas.TradeOfferCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new P2P trade offer for SLH_BNB or SLH_TON.
    """
    # Ensure wallet exists
    wallet = db.get(models.Wallet, payload.telegram_id)
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")

    offer = models.TradeOffer(
        seller_telegram_id=payload.telegram_id,
        buyer_telegram_id=None,
        token_symbol=payload.token_symbol,
        amount=payload.amount,
        price_bnb=payload.price_bnb,
        status="ACTIVE",
    )
    db.add(offer)
    db.commit()
    db.refresh(offer)
    logger.info(
        "Created offer id=%s seller=%s token=%s amount=%s price_bnb=%s",
        offer.id,
        payload.telegram_id,
        payload.token_symbol,
        payload.amount,
        payload.price_bnb,
    )
    return offer


@router.post("/offers/{offer_id}/cancel")
def cancel_offer(
    offer_id: int,
    telegram_id: str,
    db: Session = Depends(get_db),
):
    """
    Cancel an active offer (only by the seller).
    """
    offer = db.get(models.TradeOffer, offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")

    if offer.seller_telegram_id != telegram_id:
        raise HTTPException(status_code=403, detail="Not authorized to cancel this offer")

    if offer.status != "ACTIVE":
        raise HTTPException(status_code=400, detail="Offer is not active")

    offer.status = "CANCELLED"
    db.commit()
    return {"status": "cancelled", "offer_id": offer_id}


@router.post("/offers/{offer_id}/mark-paid")
def mark_offer_paid(
    offer_id: int,
    buyer_telegram_id: str,
    db: Session = Depends(get_db),
):
    """
    Mark an offer as 'PENDING_PAYMENT' by a specific buyer (soft reservation).
    """
    offer = db.get(models.TradeOffer, offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")

    if offer.status != "ACTIVE":
        raise HTTPException(status_code=400, detail="Offer is not active")

    offer.status = "PENDING_PAYMENT"
    offer.buyer_telegram_id = buyer_telegram_id
    db.commit()
    return {"status": "pending_payment", "offer_id": offer_id, "buyer_telegram_id": buyer_telegram_id}


@router.post("/offers/{offer_id}/mark-complete")
def mark_offer_complete(
    offer_id: int,
    telegram_id: str,
    db: Session = Depends(get_db),
):
    """
    Mark an offer as completed. Only the seller can confirm completion.
    """
    offer = db.get(models.TradeOffer, offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")

    if offer.seller_telegram_id != telegram_id:
        raise HTTPException(status_code=403, detail="Not authorized to complete this offer")

    if offer.status not in ("PENDING_PAYMENT", "ACTIVE"):
        raise HTTPException(status_code=400, detail="Offer cannot be completed")

    offer.status = "COMPLETED"
    db.commit()
    return {"status": "completed", "offer_id": offer_id}


@router.get("/summary", response_model=schemas.MarketSummary)
def market_summary(db: Session = Depends(get_db)):
    """
    Lightweight stats for the frontend.
    """
    total_active = db.scalar(
        select(func.count(models.TradeOffer.id)).where(models.TradeOffer.status == "ACTIVE")
    ) or 0

    token_rows = db.execute(
        select(models.TradeOffer.token_symbol, func.avg(models.TradeOffer.price_bnb))
        .where(models.TradeOffer.status == "ACTIVE")
        .group_by(models.TradeOffer.token_symbol)
    ).all()

    tokens = [row[0] for row in token_rows]
    avg_price_by_token = {row[0]: float(row[1]) for row in token_rows}

    return schemas.MarketSummary(
        active_offers=total_active,
        tokens=tokens,
        avg_price_by_token=avg_price_by_token,
    )
