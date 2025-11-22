from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models, schemas
from ..blockchain_service import blockchain_service
from ..ton_service import ton_service
from ..config import settings

router = APIRouter(prefix="/api/wallet", tags=["wallet"])


@router.post("/register", response_model=schemas.WalletOut)
def register_wallet(payload: schemas.WalletRegisterIn, db: Session = Depends(get_db)):
    wallet = db.get(models.Wallet, payload.telegram_id)
    if wallet is None:
        wallet = models.Wallet(
            telegram_id=payload.telegram_id,
            username=payload.username,
            first_name=payload.first_name,
            last_name=payload.last_name,
            bnb_address=payload.bnb_address,
            slh_address=payload.slh_address,
            slh_ton_address=payload.slh_ton_address,
        )
        db.add(wallet)
    else:
        wallet.username = payload.username or wallet.username
        wallet.first_name = payload.first_name or wallet.first_name
        wallet.last_name = payload.last_name or wallet.last_name
        if payload.bnb_address:
            wallet.bnb_address = payload.bnb_address
        if payload.slh_address:
            wallet.slh_address = payload.slh_address
        if payload.slh_ton_address:
            wallet.slh_ton_address = payload.slh_ton_address
    db.commit()
    db.refresh(wallet)
    return wallet


@router.get("/by-telegram/{telegram_id}", response_model=schemas.WalletDetailsResponse)
def get_wallet_by_telegram(telegram_id: str, db: Session = Depends(get_db)):
    wallet = db.get(models.Wallet, telegram_id)
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return schemas.WalletDetailsResponse(
        wallet=wallet,
        has_bnb=bool(wallet.bnb_address),
        has_slh_bnb=bool(wallet.slh_address),
        has_slh_ton=bool(wallet.slh_ton_address),
    )


@router.get("/{telegram_id}/balances", response_model=schemas.BalanceResponse)
async def get_balances(telegram_id: str, db: Session = Depends(get_db)):
    wallet = db.get(models.Wallet, telegram_id)
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")

    bnb_address = wallet.bnb_address or wallet.slh_address or ""
    slh_address = wallet.slh_address or wallet.bnb_address or ""

    chain_balances = await blockchain_service.get_balances(bnb_address, slh_address)
    slh_ton_balance = 0.0
    if wallet.slh_ton_address:
        slh_ton_balance = await ton_service.get_slh_ton_balance(wallet.slh_ton_address)

    return schemas.BalanceResponse(
        telegram_id=wallet.telegram_id,
        bnb_address=bnb_address or None,
        slh_address=slh_address or None,
        slh_ton_address=wallet.slh_ton_address,
        bnb=float(chain_balances.get("bnb", 0.0)),
        slh_bnb=float(chain_balances.get("slh", 0.0)),
        slh_ton=float(slh_ton_balance),
        slh_ton_factor=float(settings.slh_ton_factor),
    )
