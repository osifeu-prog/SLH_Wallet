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
    # ✅ ולידציה נוספת - אורך כתובות
    if payload.bnb_address and len(payload.bnb_address) > 200:
        raise HTTPException(status_code=400, detail="BNB address too long")
    
    if payload.slh_address and len(payload.slh_address) > 200:
        raise HTTPException(status_code=400, detail="SLH address too long")

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
    if not telegram_id or len(telegram_id) > 50:
        raise HTTPException(status_code=400, detail="Invalid telegram ID")
        
    wallet = db.get(models.Wallet, telegram_id)
    if not wallet:
        raise HTTPException(status_code=404, detail="User not found")
    return wallet


@router.get("/exists/{telegram_id}")
def check_wallet_exists(
    telegram_id: str,
    db: Session = Depends(get_db),
):
    """✅ endpoint נוסף לבדיקה אם משתמש רשום"""
    if not telegram_id or len(telegram_id) > 50:
        return {"exists": False}
        
    wallet = db.get(models.Wallet, telegram_id)
    return {"exists": wallet is not None}
