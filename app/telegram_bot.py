
import json
import logging
from typing import Optional

import aiohttp
from fastapi import APIRouter, HTTPException, Request
from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

from .config import settings

logger = logging.getLogger("slh_wallet.bot")

router = APIRouter()

_application: Optional[Application] = None


async def _build_application() -> Application:
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")

    application = (
        ApplicationBuilder()
        .token(settings.telegram_bot_token)
        .concurrent_updates(True)
        .build()
    )

    # Handlers
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("wallet", cmd_wallet))
    application.add_handler(CommandHandler("bank", cmd_bank))
    application.add_handler(CommandHandler("balances", cmd_balances))

    # חשוב: initialize + start כדי שטלגרם לא יזרוק שגיאה
    await application.initialize()
    await application.start()

    return application


async def get_application() -> Application:
    global _application
    if _application is None:
        _application = await _build_application()
        logger.info("Telegram Application initialized successfully")
    return _application


# -------- Bot command handlers --------

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user or not update.message:
        return

    telegram_id = user.id
    username = f"@{user.username}" if user.username else user.full_name

    text = (
        "ברוך הבא ל-SLH Wallet 🚀\n\n"
        "כאן אתה יכול לפתוח ארנק קהילתי, לראות יתרות BNB/SLH ולסחור עם חברי הקהילה.\n\n"
        "פקודות זמינות:\n"
        "/wallet - קישור לעמוד הארנק שלך\n"
        "/balances - הצגת יתרות הארנק שלך\n"
        "/bank - עדכון פרטי בנק לקבלת תשלומים\n"
    )

    await update.message.reply_text(text)
    logger.info("BOT /start from %s(%s)", username, telegram_id)


async def cmd_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user or not update.message:
        return

    telegram_id = user.id
    username = f"@{user.username}" if user.username else user.full_name

    base = settings.base_url or settings.frontend_api_base
    base = base.rstrip("/")
    url = f"{base}/wallet?telegram_id={telegram_id}"

    text = (
        "הנה הקישור לעמוד הארנק שלך:\n"
        f"{url}\n\n"
        "שם תוכל לחבר MetaMask, לעדכן כתובות ופרטי בנק."
    )
    await update.message.reply_text(text)
    logger.info("BOT /wallet from %s(%s)", username, telegram_id)


async def cmd_bank(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user or not update.message:
        return

    telegram_id = user.id
    username = f"@{user.username}" if user.username else user.full_name

    base = settings.base_url or settings.frontend_api_base
    base = base.rstrip("/")
    url = f"{base}/wallet?telegram_id={telegram_id}#bank"

    text = (
        "לעדכון פרטי הבנק שלך לקבלת תשלומים, היכנס לעמוד הארנק:\n"
        f"{url}"
    )
    await update.message.reply_text(text)
    logger.info("BOT /bank from %s(%s)", username, telegram_id)


async def cmd_balances(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user or not update.message:
        return

    telegram_id = user.id
    username = f"@{user.username}" if user.username else user.full_name

    api_base = settings.frontend_api_base or settings.base_url
    api_base = api_base.rstrip("/")
    url = f"{api_base}/api/wallet/{telegram_id}/balances"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=15) as resp:
                if resp.status != 200:
                    await update.message.reply_text("לא הצלחתי להביא את היתרות כרגע. נסה שוב מאוחר יותר.")
                    logger.error("Balances HTTP %s for %s", resp.status, telegram_id)
                    return
                data = await resp.json()
    except Exception as e:
        logger.error("Error calling balances API for %s: %s", telegram_id, e)
        await update.message.reply_text("אירעה שגיאה בזמן הבאת היתרות. נסה שוב מאוחר יותר.")
        return

    if not data.get("success", False):
        await update.message.reply_text("לא קיימות כתובות רשומות לארנק שלך. היכנס קודם לעמוד הארנק באתר.")
        return

    bnb = data.get("bnb_balance", 0.0)
    slh = data.get("slh_balance", 0.0)
    bnb_address = data.get("bnb_address") or "לא מוגדר"
    slh_address = data.get("slh_address") or "לא מוגדר"

    text = (
        "📊 יתרות הארנק שלך:\n"
        f"BNB: {bnb:.6f}\n"
        f"SLH: {slh:.6f}\n\n"
        f"BNB address: {bnb_address}\n"
        f"SLH address: {slh_address}"
    )

    await update.message.reply_text(text)
    logger.info("BOT /balances from %s(%s)", username, telegram_id)


# -------- FastAPI webhook --------

@router.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    """
    נקודת כניסה לעדכוני Webhook מהבוט של טלגרם.
    """
    try:
        body = await request.body()
        if not body:
            raise HTTPException(status_code=400, detail="Empty body")

        data = json.loads(body.decode("utf-8"))

        app = await get_application()
        update = Update.de_json(data, app.bot)
        await app.process_update(update)

        return {"ok": True}
    except json.JSONDecodeError:
        logger.error("Invalid JSON in webhook")
        raise HTTPException(status_code=400, detail="Invalid JSON")
    except Exception as e:
        logger.error("Error processing webhook: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")
