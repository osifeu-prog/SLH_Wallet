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
    """
    רישום / עדכון ארנק:
    - אם לא קיים – יוצר רשומה חדשה
    - אם קיים – מעדכן רק שדות שהתקבלו (לא מוחק ערכים קיימים)
    """
    telegram_id = (payload.telegram_id or "").strip()
    if not telegram_id or len(telegram_id) > 50:
        raise HTTPException(status_code=400, detail="Invalid telegram ID")

    # ולידציה בסיסית לאורך שדות
    if payload.username and len(payload.username) > 100:
        raise HTTPException(status_code=400, detail="Username too long")
    if payload.first_name and len(payload.first_name) > 100:
        raise HTTPException(status_code=400, detail="First name too long")
    if payload.last_name and len(payload.last_name) > 100:
        raise HTTPException(status_code=400, detail="Last name too long")
    if payload.bnb_address and len(payload.bnb_address) > 200:
        raise HTTPException(status_code=400, detail="BNB address too long")
    if payload.slh_address and len(payload.slh_address) > 200:
        raise HTTPException(status_code=400, detail="SLH address too long")
    if payload.bank_account_number and len(payload.bank_account_number) > 100:
        raise HTTPException(status_code=400, detail="Bank account number too long")

    wallet = db.get(models.Wallet, telegram_id)

    if wallet is None:
        wallet = models.Wallet(telegram_id=telegram_id)
        db.add(wallet)
        logger.info("Created new wallet for Telegram ID: %s", telegram_id)
    else:
        logger.info("Updating existing wallet for Telegram ID: %s", telegram_id)

    # עדכון כל השדות שנשלחו בפועל
    update_fields = [
        "username",
        "first_name",
        "last_name",
        "bnb_address",
        "slh_address",
        "bank_account_number",
        "bank_name",
        "bank_branch",
        "bank_holder_name",
    ]
    for field in update_fields:
        value = getattr(payload, field, None)
        if value is not None:
            setattr(wallet, field, value)

    # אם אין slh_address אבל יש bnb_address – נשתמש בו גם ככתובת SLH
    if not wallet.slh_address and wallet.bnb_address:
        wallet.slh_address = wallet.bnb_address

    db.commit()
    db.refresh(wallet)

    return schemas.WalletOut.from_orm(wallet)


@router.get("/by-telegram/{telegram_id}", response_model=schemas.WalletOut)
def get_wallet_by_telegram(
    telegram_id: str,
    db: Session = Depends(get_db),
):
    telegram_id = (telegram_id or "").strip()
    if not telegram_id or len(telegram_id) > 50:
        raise HTTPException(status_code=400, detail="Invalid telegram ID")

    wallet = db.get(models.Wallet, telegram_id)
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")

    return schemas.WalletOut.from_orm(wallet)


@router.get("/exists/{telegram_id}")
def check_wallet_exists(
    telegram_id: str,
    db: Session = Depends(get_db),
):
    telegram_id = (telegram_id or "").strip()
    if not telegram_id or len(telegram_id) > 50:
        return {"exists": False}

    wallet = db.get(models.Wallet, telegram_id)
    return {"exists": wallet is not None}


@router.get("/{telegram_id}/balances", response_model=schemas.BalanceResponse)
async def get_wallet_balances(
    telegram_id: str,
    db: Session = Depends(get_db),
):
    telegram_id = (telegram_id or "").strip()
    if not telegram_id or len(telegram_id) > 50:
        raise HTTPException(status_code=400, detail="Invalid telegram ID")

    wallet = db.get(models.Wallet, telegram_id)
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")

    bnb_address = wallet.bnb_address or ""
    slh_address = wallet.slh_address or wallet.bnb_address or ""

    if not bnb_address and not slh_address:
        raise HTTPException(status_code=400, detail="Wallet has no blockchain addresses")

    balances = await blockchain_service.get_balances(bnb_address, slh_address)

    return schemas.BalanceResponse(
        telegram_id=telegram_id,
        bnb_balance=balances.get("bnb", 0.0),
        slh_balance=balances.get("slh", 0.0),
        bnb_address=bnb_address,
        slh_address=slh_address,
        success=True,
    )


@router.get("/details/{telegram_id}")
def get_wallet_details(
    telegram_id: str,
    db: Session = Depends(get_db),
):
    """
    Endpoint נוח ל-frontend:
    - wallet: כל פרטי הארנק
    - flags: האם יש MetaMask / פרטי בנק
    """
    telegram_id = (telegram_id or "").strip()
    if not telegram_id or len(telegram_id) > 50:
        raise HTTPException(status_code=400, detail="Invalid telegram ID")

    wallet = db.get(models.Wallet, telegram_id)
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")

    wallet_out = schemas.WalletOut.from_orm(wallet)

    return {
        "wallet": wallet_out,
        "has_metamask": bool(wallet_out.bnb_address),
        "has_bank_info": bool(wallet_out.bank_account_number),
        "registration_date": wallet_out.created_at,
    }
