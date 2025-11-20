
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .database import get_db
from .models import User, Wallet, TransactionLog
from .schemas import WalletRegisterIn, WalletOut
from .logging_utils import log_event

router = APIRouter(prefix="/api/wallet", tags=["wallet"])


@router.post("/register", response_model=WalletOut)
async def register_wallet(payload: WalletRegisterIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.telegram_id == payload.telegram_id).first()
    if not user:
        user = User(
            telegram_id=payload.telegram_id,
            username=payload.username,
            first_name=payload.first_name,
        )
        db.add(user)
        db.flush()

    wallet = db.query(Wallet).filter(Wallet.user_id == user.id).first()
    if not wallet:
        wallet = Wallet(user_id=user.id)

    wallet.bnb_address = payload.bnb_address or wallet.bnb_address
    wallet.slh_address = payload.slh_address or wallet.slh_address

    db.add(wallet)
    db.add(
        TransactionLog(
            user_id=user.id,
            kind="wallet_register",
            description=f"Wallet register/update for telegram_id={payload.telegram_id}",
        )
    )
    db.commit()
    db.refresh(wallet)

    await log_event("wallet", f"Wallet registered/updated for telegram_id={payload.telegram_id}")
    return WalletOut(
        telegram_id=user.telegram_id,
        username=user.username,
        first_name=user.first_name,
        bnb_address=wallet.bnb_address,
        slh_address=wallet.slh_address,
        created_at=wallet.created_at,
        updated_at=wallet.updated_at,
    )


@router.get("/by-telegram/{telegram_id}", response_model=WalletOut)
async def get_wallet_by_telegram(telegram_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    wallet = db.query(Wallet).filter(Wallet.user_id == user.id).first()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")

    return WalletOut(
        telegram_id=user.telegram_id,
        username=user.username,
        first_name=user.first_name,
        bnb_address=wallet.bnb_address,
        slh_address=wallet.slh_address,
        created_at=wallet.created_at,
        updated_at=wallet.updated_at,
    )
