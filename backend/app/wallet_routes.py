
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .db import get_db
from . import models, schemas
from .logger import logger

router = APIRouter(prefix="/api/wallet", tags=["Wallet"])

@router.post("/register", response_model=schemas.WalletOut)
def register_wallet(payload: schemas.WalletRegisterIn, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.telegram_id == payload.telegram_id).first()
    if not user:
        user = models.User(
            telegram_id=payload.telegram_id,
            username=payload.username,
            first_name=payload.first_name,
        )
        db.add(user)
        db.flush()
    wallet = user.wallet
    if not wallet:
        wallet = models.Wallet(
            owner=user,
            bnb_address=payload.bnb_address,
            slh_address=payload.slh_address,
        )
        db.add(wallet)
    else:
        wallet.bnb_address = payload.bnb_address or wallet.bnb_address
        wallet.slh_address = payload.slh_address or wallet.slh_address
    db.commit()
    db.refresh(wallet)
    logger.info(f"[WALLET] Registered/updated wallet for telegram_id={payload.telegram_id}")
    return schemas.WalletOut(
        telegram_id=user.telegram_id,
        username=user.username,
        first_name=user.first_name,
        bnb_address=wallet.bnb_address,
        slh_address=wallet.slh_address,
        created_at=wallet.created_at,
        updated_at=wallet.updated_at,
    )

@router.get("/by-telegram/{telegram_id}", response_model=schemas.WalletOut)
def get_wallet_by_telegram(telegram_id: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.telegram_id == telegram_id).first()
    if not user or not user.wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    wallet = user.wallet
    return schemas.WalletOut(
        telegram_id=user.telegram_id,
        username=user.username,
        first_name=user.first_name,
        bnb_address=wallet.bnb_address,
        slh_address=wallet.slh_address,
        created_at=wallet.created_at,
        updated_at=wallet.updated_at,
    )
