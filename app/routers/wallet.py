
from __future__ import annotations

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from .. import models, schemas

logger = logging.getLogger("slh_wallet.wallet_router")

router = APIRouter(tags=["wallet"])

templates = Jinja2Templates(directory="frontend")


@router.get("/u/{telegram_id}", response_class=HTMLResponse)
async def personal_hub(
    request: Request,
    telegram_id: str = Path(..., description="Telegram ID of the user"),
    db: Session = Depends(get_db),
):
    wallet = db.get(models.Wallet, telegram_id)
    if not wallet:
        # Show a simple "not registered" page with hint to use the bot
        return templates.TemplateResponse(
            "user_not_found.html",
            {
                "request": request,
                "telegram_id": telegram_id,
                "bot_url": settings.bot_username and f"https://t.me/{settings.bot_username}" or "",
            },
        )

    # Compute QR URL (for now just use /u/{telegram_id})
    base = settings.frontend_api_base or settings.base_url
    user_url = f"{base}/u/{telegram_id}"

    return templates.TemplateResponse(
        "user.html",
        {
            "request": request,
            "wallet": wallet,
            "user_url": user_url,
            "community_link": settings.community_link,
            "slh_token_address": settings.slh_token_address,
        },
    )


@router.post("/api/wallet/register", response_model=schemas.WalletOut)
def register_wallet(
    payload: schemas.WalletRegisterIn,
    db: Session = Depends(get_db),
):
    """
    Upsert wallet record.
    This endpoint is intended to be called *from the Telegram bot only*.

    If wallet exists -> update fields that were provided.
    If not -> create new wallet row.
    """
    logger.info("Register/update wallet %s", payload.telegram_id)

    wallet = db.get(models.Wallet, payload.telegram_id)
    created = False
    if not wallet:
        wallet = models.Wallet(telegram_id=payload.telegram_id)
        created = True

    # update basic identity
    wallet.username = payload.username or wallet.username
    wallet.first_name = payload.first_name or wallet.first_name
    wallet.last_name = payload.last_name or wallet.last_name

    # update addresses if provided
    if payload.bnb_address is not None:
        wallet.bnb_address = payload.bnb_address
    if payload.slh_address is not None:
        wallet.slh_address = payload.slh_address
    if payload.slh_ton_address is not None:
        wallet.slh_ton_address = payload.slh_ton_address

    # bank details
    if payload.bank_account_name is not None:
        wallet.bank_account_name = payload.bank_account_name
    if payload.bank_account_number is not None:
        wallet.bank_account_number = payload.bank_account_number

    if created:
        db.add(wallet)

    db.commit()
    db.refresh(wallet)
    return wallet


@router.get("/api/wallet/by-telegram/{telegram_id}", response_model=schemas.WalletOut)
def get_wallet_by_telegram(
    telegram_id: str,
    db: Session = Depends(get_db),
):
    wallet = db.get(models.Wallet, telegram_id)
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return wallet


@router.get("/api/wallet/{telegram_id}/balances", response_model=schemas.WalletBalancesOut)
def get_balances(
    telegram_id: str,
    db: Session = Depends(get_db),
):
    wallet = db.get(models.Wallet, telegram_id)
    if not wallet:
        return schemas.WalletBalancesOut(success=False)

    # For now we keep on-chain queries simple / optional –
    # if we don't have BscScan API key, just return 0 balances.
    bnb_balance = 0.0
    slh_onchain = 0.0

    # TODO: plug real BNB/SLH/Ton queries via BscScan / TON API if keys exist

    total_slh = wallet.internal_slh_balance + slh_onchain

    return schemas.WalletBalancesOut(
        success=True,
        bnb_address=wallet.bnb_address,
        slh_address=wallet.slh_address,
        slh_ton_address=wallet.slh_ton_address,
        internal_slh_balance=wallet.internal_slh_balance,
        internal_slh_locked=wallet.internal_slh_locked,
        bnb_balance=bnb_balance,
        slh_balance_onchain=slh_onchain,
        slh_balance_total=total_slh,
    )


@router.get("/wallet", response_class=HTMLResponse)
async def legacy_wallet_redirect(
    request: Request,
    telegramid: str | None = None,
    telegram_id: str | None = None,
):
    """
    Legacy /wallet endpoint.
    If a telegram id is provided, redirect the user to /u/{telegram_id}.
    Otherwise show a simple info page asking to start from the bot.
    """
    tid = telegram_id or telegramid
    if tid:
        base = settings.frontend_api_base or settings.base_url
        # Frontend/JS can redirect, here we show a minimal page with link
        return templates.TemplateResponse(
            "wallet_redirect.html",
            {
                "request": request,
                "user_url": f"{base}/u/{tid}",
                "telegram_id": tid,
            },
        )

    return templates.TemplateResponse(
        "wallet_ask_telegram.html",
        {
            "request": request,
            "bot_url": settings.bot_username and f"https://t.me/{settings.bot_username}" or "",
        },
    )
