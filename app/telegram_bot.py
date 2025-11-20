from __future__ import annotations

import json
import logging
from typing import Optional

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from telegram import Update, User as TgUser
from telegram.ext import Application, ApplicationBuilder, CommandHandler, ContextTypes

from .config import get_settings
from .database import SessionLocal
from .logging_utils import log_event
from .models import User, Wallet

logger = logging.getLogger("slh_wallet.telegram")

router = APIRouter()
settings = get_settings()


class TelegramUpdate(BaseModel):
    update_id: Optional[int] = None


_bot_app: Optional[Application] = None


async def get_bot_application() -> Application:
    """
    Lazily create and cache the python-telegram-bot Application used for webhook processing.
    """
    global _bot_app
    if _bot_app is None:
        if not settings.TELEGRAM_BOT_TOKEN:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")

        _bot_app = (
            ApplicationBuilder()
            .token(settings.TELEGRAM_BOT_TOKEN)
            .concurrent_updates(True)
            .build()
        )

        _bot_app.add_handler(CommandHandler("start", handle_start))
        _bot_app.add_handler(CommandHandler("wallet", handle_wallet))

        await log_event("BOT", "Telegram Application instance created and handlers registered")

    return _bot_app


def _get_frontend_base_url() -> str:
    """
    Prefer FRONTEND_API_BASE, fall back to BASE_URL if needed.
    """
    base = settings.FRONTEND_API_BASE or settings.BASE_URL or ""
    return base.rstrip("/")


async def ensure_wallet_for_telegram_user(tg_user: TgUser) -> None:
    """
    Ensure that a User + Wallet row exist for the given Telegram user.
    If they already exist, their username/first_name are kept in sync.
    """
    db = SessionLocal()
    telegram_id = str(tg_user.id)
    username = tg_user.username
    first_name = tg_user.first_name

    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        created_user = False
        if user is None:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
            )
            db.add(user)
            created_user = True

        # Ensure we have a primary key for the user
        db.flush()

        changed = False
        if username and user.username != username:
            user.username = username
            changed = True
        if first_name and user.first_name != first_name:
            user.first_name = first_name
            changed = True

        wallet = (
            db.query(Wallet)
            .filter(Wallet.user_id == user.id)
            .order_by(Wallet.id.asc())
            .first()
        )

        created_wallet = False
        if wallet is None:
            wallet = Wallet(
                user_id=user.id,
                bnb_address=None,
                slh_address=None,
            )
            db.add(wallet)
            created_wallet = True

        db.commit()

        if created_user:
            await log_event("WALLET", f"Created User for telegram_id={telegram_id}")
        if created_wallet:
            await log_event("WALLET", f"Created Wallet for telegram_id={telegram_id}")
        if changed and not created_user:
            await log_event("WALLET", f"Updated profile for telegram_id={telegram_id}")

    except Exception as exc:  # noqa: BLE001
        db.rollback()
        logger.exception("ensure_wallet_for_telegram_user failed: %s", exc)
        await log_event("ERROR", f"ensure_wallet_for_telegram_user failed: {exc}")
    finally:
        db.close()


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tg_user = update.effective_user
    chat = update.effective_chat

    if not tg_user or not chat:
        return

    await log_event(
        "BOT",
        f"/start from @{tg_user.username}({tg_user.id})"
    )

    # Auto-create / sync wallet for this Telegram user
    await ensure_wallet_for_telegram_user(tg_user)

    frontend_base = _get_frontend_base_url()
    wallet_url = f"{frontend_base}/#wallet" if frontend_base else "#wallet"
    landing_url = frontend_base or "/"
    community = settings.COMMUNITY_LINK or ""

    text_lines = [
        f"שלום @{tg_user.username or tg_user.first_name}! 🌐",
        "",
        "ברוך הבא ל-SLH Wallet 2.0.",
        "",
        "כאן נרכז בהמשך:",
        "• ארנק BNB/SLH אישי",
        "• כתובת SLH מזוהה למערכת",
        "• חיבור לכלי המסחר והקהילה.",
        "",
        "פתיחת ארנק / התחברות:",
        f"➡️ {landing_url}",
    ]

    if community:
        text_lines.append(f"לקבוצת הקהילה: {community}")

    text = "\n".join(text_lines)

    await context.bot.send_message(chat_id=chat.id, text=text)


async def handle_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tg_user = update.effective_user
    chat = update.effective_chat

    if not tg_user or not chat:
        return

    await log_event(
        "BOT",
        f"/wallet from @{tg_user.username}({tg_user.id})"
    )

    # Auto-create / sync wallet for this Telegram user
    await ensure_wallet_for_telegram_user(tg_user)

    frontend_base = _get_frontend_base_url()
    wallet_url = f"{frontend_base}/#wallet" if frontend_base else "#wallet"

    lines = [
        "להגדרת ארנק / עדכון פרטים:",
        f"➡️ {wallet_url}",
    ]

    await context.bot.send_message(chat_id=chat.id, text="\n".join(lines))


@router.post("/telegram/webhook", response_class=JSONResponse)
async def telegram_webhook(request: Request) -> JSONResponse:
    # Telegram always sends JSON; if this endpoint is hit manually without a body,
    # avoid raising JSONDecodeError.
    raw_body = await request.body()
    if not raw_body:
        raise HTTPException(status_code=400, detail="Empty body")

    try:
        data = json.loads(raw_body.decode("utf-8"))
    except json.JSONDecodeError as exc:  # noqa: B902
        logger.warning("Failed to decode Telegram update JSON: %s", exc)
        raise HTTPException(status_code=400, detail="Invalid JSON body") from exc

    app = await get_bot_application()
    update = Update.de_json(data, app.bot)

    await app.process_update(update)

    await log_event("WEB", "POST /telegram/webhook -> 200 (update processed)")

    return JSONResponse({"ok": True})
