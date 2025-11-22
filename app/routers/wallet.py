import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..blockchain_service import blockchain_service
from ..ton_service import ton_service
from ..config import settings

logger = logging.getLogger("slh_wallet.wallet_router")

router = APIRouter(prefix="/api/wallet", tags=["wallet"])


@router.post("/register", response_model=schemas.WalletOut)
def register_wallet(
    payload: schemas.WalletRegisterIn,
    db: Session = Depends(get_db),
):
    """
    Create or update a wallet profile for a Telegram user.
    Intended to be called from the Telegram bot.
    """
    if not payload.telegram_id or len(payload.telegram_id) > 50:
        raise HTTPException(status_code=400, detail="Invalid telegram ID")

    wallet = db.get(models.Wallet, payload.telegram_id)
    created = False
    if wallet is None:
        wallet = models.Wallet(telegram_id=payload.telegram_id)
        created = True

    wallet.username = payload.username or wallet.username
    wallet.first_name = payload.first_name or wallet.first_name
    wallet.last_name = payload.last_name or wallet.last_name
    wallet.bnb_address = payload.bnb_address or wallet.bnb_address
    wallet.slh_address = payload.slh_address or wallet.slh_address
    wallet.slh_ton_address = payload.slh_ton_address or wallet.slh_ton_address
    wallet.bank_account_number = payload.bank_account_number or wallet.bank_account_number
    wallet.bank_account_name = payload.bank_account_name or wallet.bank_account_name

    if created:
        db.add(wallet)

    db.commit()
    db.refresh(wallet)

    logger.info("Wallet %s for telegram_id=%s", "created" if created else "updated", payload.telegram_id)
    return wallet


@router.post("/link-address", response_model=schemas.WalletOut)
def link_address(
    telegram_id: str,
    kind: str,
    address: str,
    db: Session = Depends(get_db),
):
    """
    Link an address (BNB / SLH_BNB / SLH_TON) to a wallet.
    kind: 'bnb' | 'slh' | 'slh_ton'
    """
    wallet = db.get(models.Wallet, telegram_id)
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")

    kind = kind.lower()
    if kind == "bnb":
        wallet.bnb_address = address
    elif kind == "slh":
        wallet.slh_address = address
    elif kind in ("slh_ton", "ton"):
        wallet.slh_ton_address = address
    else:
        raise HTTPException(status_code=400, detail="Unknown address kind")

    db.commit()
    db.refresh(wallet)
    return wallet


@router.get("/{telegram_id}/balances", response_model=schemas.BalanceResponse)
async def get_balances(
    telegram_id: str,
    db: Session = Depends(get_db),
):
    """
    Resolve a wallet by telegram_id and return live balances from BNB / SLH_BNB / SLH_TON.
    """
    wallet = db.get(models.Wallet, telegram_id)
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")

    # Fetch BNB + SLH_BNB
    bnb_address = wallet.bnb_address or wallet.slh_address
    slh_address = wallet.slh_address or wallet.bnb_address

    chain_balances = await blockchain_service.get_balances(bnb_address or "", slh_address or "")

    # Fetch SLH_TON
    slh_ton_balance = 0.0
    if wallet.slh_ton_address:
        slh_ton_balance = await ton_service.get_slh_ton_balance(wallet.slh_ton_address)

    return schemas.BalanceResponse(
        telegram_id=wallet.telegram_id,
        bnb_balance=chain_balances.get("bnb", 0.0),
        slh_balance=chain_balances.get("slh", 0.0),
        slh_ton_balance=slh_ton_balance,
        slh_ton_factor=settings.slh_ton_factor,
        bnb_address=wallet.bnb_address,
        slh_address=wallet.slh_address,
        slh_ton_address=wallet.slh_ton_address,
        success=True,
    )


@router.get("/by-telegram/{telegram_id}", response_model=schemas.WalletDetailsResponse)
def get_wallet_by_telegram(
    telegram_id: str,
    db: Session = Depends(get_db),
):
    """
    Return full wallet profile + some flags for the UI/bot.
    """
    if not telegram_id or len(telegram_id) > 50:
        raise HTTPException(status_code=400, detail="Invalid telegram ID")

    wallet = db.get(models.Wallet, telegram_id)
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")

    return schemas.WalletDetailsResponse(
        wallet=wallet,
        has_bnb_address=bool(wallet.bnb_address),
        has_slh_address=bool(wallet.slh_address),
        has_slh_ton_address=bool(wallet.slh_ton_address),
        has_bank_info=bool(wallet.bank_account_number),
        registration_date=wallet.created_at,
    )
