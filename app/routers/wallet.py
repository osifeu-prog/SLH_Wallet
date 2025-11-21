from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/wallet", tags=["wallet"])


@router.post("/register", response_model=schemas.WalletOut)
def register_wallet(
    payload: schemas.WalletRegisterIn,
    db: Session = Depends(get_db),
):
    wallet = db.get(models.Wallet, payload.telegram_id)

    if not wallet:
        wallet = models.Wallet(telegram_id=payload.telegram_id)
        db.add(wallet)

    if payload.username is not None:
        wallet.username = payload.username
    if payload.first_name is not None:
        wallet.first_name = payload.first_name
    if payload.bnb_address is not None:
        wallet.bnb_address = payload.bnb_address
    if payload.slh_address is not None:
        wallet.slh_address = payload.slh_address

    db.commit()
    db.refresh(wallet)
    return wallet


@router.get("/by-telegram/{telegram_id}", response_model=schemas.WalletOut)
def get_wallet_by_telegram(
    telegram_id: str,
    db: Session = Depends(get_db),
):
    wallet = db.get(models.Wallet, telegram_id)
    if not wallet:
        raise HTTPException(status_code=404, detail="User not found")
    return wallet
