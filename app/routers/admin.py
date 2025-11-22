from typing import List

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models, schemas
from ..config import settings

router = APIRouter(prefix="/api/admin", tags=["admin"])


def require_admin_token(x_admin_token: str = Header(..., alias="X-Admin-Token")):
    if not settings.admin_dash_token or x_admin_token != settings.admin_dash_token:
        raise HTTPException(status_code=403, detail="Forbidden")
    return True


@router.get("/summary", response_model=schemas.AdminSummary)
def admin_summary(
    _: bool = Depends(require_admin_token),
    db: Session = Depends(get_db),
):
    total_wallets = db.query(func.count(models.Wallet.telegram_id)).scalar() or 0
    total_referrals = db.query(func.count(models.Referral.id)).scalar() or 0
    total_trade_offers = db.query(func.count(models.TradeOffer.id)).scalar() or 0
    active_trade_offers = (
        db.query(func.count(models.TradeOffer.id))
        .filter(models.TradeOffer.status == "ACTIVE")
        .scalar()
        or 0
    )

    last_offers = (
        db.query(models.TradeOffer)
        .order_by(models.TradeOffer.created_at.desc())
        .limit(20)
        .all()
    )
    return schemas.AdminSummary(
        total_wallets=int(total_wallets),
        total_referrals=int(total_referrals),
        total_trade_offers=int(total_trade_offers),
        active_trade_offers=int(active_trade_offers),
        last_offers=last_offers,
    )
