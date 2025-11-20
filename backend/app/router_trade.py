
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .database import get_db
from .models import TradeOffer, TransactionLog, User
from .schemas import TradeOfferOut
from .logging_utils import log_event

router = APIRouter(prefix="/api/trade", tags=["trade"])


@router.get("/offers", response_model=list[TradeOfferOut])
async def list_offers(db: Session = Depends(get_db)):
    offers = db.query(TradeOffer).filter(TradeOffer.is_active == True).order_by(TradeOffer.created_at.desc()).all()
    return offers


@router.post("/create-offer", response_model=TradeOfferOut)
async def create_offer(
    telegram_id: str,
    token_symbol: str,
    amount: float,
    price_bnb: float,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        user = User(telegram_id=telegram_id)
        db.add(user)
        db.flush()

    offer = TradeOffer(
        maker_user_id=user.id,
        token_symbol=token_symbol,
        amount=amount,
        price_bnb=price_bnb,
        is_active=True,
    )
    db.add(offer)
    db.add(
        TransactionLog(
            user_id=user.id,
            kind="trade",
            description=f"Created offer id={offer.id} token={token_symbol} amount={amount} price={price_bnb}",
        )
    )
    db.commit()
    db.refresh(offer)

    await log_event("trade", f"Offer created by telegram_id={telegram_id}, id={offer.id}")
    return offer
