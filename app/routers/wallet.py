import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..blockchain_service import blockchain_service

logger = logging.getLogger("slh_wallet.wallet_router")

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


@router.get("/{telegram_id}/balances")
async def get_wallet_balances(
    telegram_id: str,
    db: Session = Depends(get_db),
):
    """✅ endpoint חדש - מחזיר יתרות מהבלוקצ'יין"""
    if not telegram_id or len(telegram_id) > 50:
        raise HTTPException(status_code=400, detail="Invalid telegram ID")
        
    wallet = db.get(models.Wallet, telegram_id)
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    # אם אין כתובת BNB, נשתמש ב-SLH ולהפך
    bnb_address = wallet.bnb_address or ""
    slh_address = wallet.slh_address or wallet.bnb_address or ""
    
    try:
        balances = await blockchain_service.get_balances(bnb_address, slh_address)
        
        return {
            "telegram_id": telegram_id,
            "bnb_balance": balances["bnb"],
            "slh_balance": balances["slh"],
            "bnb_address": bnb_address,
            "slh_address": slh_address,
            "success": True
        }
    except Exception as e:
        logger.error("Error getting balances for %s: %s", telegram_id, e)
        raise HTTPException(status_code=500, detail="Error fetching blockchain data")
