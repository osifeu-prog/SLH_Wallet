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

    # רישום פקודות
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("wallet", cmd_wallet))
    application.add_handler(CommandHandler("balances", cmd_balances))
    application.add_handler(CommandHandler("bank", cmd_bank))
    application.add_handler(CommandHandler("sell", cmd_sell))
    application.add_handler(CommandHandler("market", cmd_market))

    # חשוב: initialize + start אחרת טלגרם זורק שגיאה
    await application.initialize()
    await application.start()

    return application


async def get_application() -> Application:
    global _application
    if _application is None:
        _application = await _build_application()
        logger.info("Telegram Application initialized successfully")
    return _application


# ===== עזר ל-HTTP ל-API =====

def _api_base() -> str:
    base = settings.frontend_api_base or settings.base_url
    return base.rstrip("/")


async def _ensure_wallet_exists(telegram_id: int, username: str, first_name: str) -> None:
    """
    דואג שתהיה רשומת ארנק ב-DB. אם קיימת – יעדכן פרטים, אם לא – ייצור.
    """
    url = f"{_api_base()}/api/wallet/register"
    payload = {
        "telegram_id": str(telegram_id),
        "username": username,
        "first_name": first_name,
        "last_name": None,
        "bnb_address": None,
        "slh_address": None,
        "bank_account_number": None,
        "bank_name": None,
        "bank_branch": None,
        "bank_holder_name": None,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=10) as resp:
                if resp.status not in (200, 201):
                    text = await resp.text()
                    logger.error("Wallet register failed [%s]: %s", resp.status, text)
    except Exception as e:
        logger.error("Wallet register error: %s", e)


# ===== הפקודות בבוט =====

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user or not update.message:
        return

    telegram_id = user.id
    username = f"@{user.username}" if user.username else user.full_name
    first_name = user.first_name or user.full_name

    await _ensure_wallet_exists(telegram_id, username, first_name)

    text = (
        "ברוך הבא ל-SLH Wallet 🚀\n\n"
        "כאן אתה יכול לפתוח ארנק קהילתי, לראות יתרות BNB/SLH ולסחור עם חברי הקהילה.\n\n"
        "פקודות זמינות:\n"
        "/wallet - תקציר הארנק שלך\n"
        "/balances - הצגת יתרות הארנק שלך\n"
        "/sell <כמות> <מחיר_BNB> - פתיחת הצעת מכירה\n"
        "/market - צפייה בהצעות הקיימות בשוק\n"
        "/bank - מידע על עדכון פרטי בנק\n"
    )

    await update.message.reply_text(text)
    logger.info("BOT /start from %s(%s)", username, telegram_id)


async def cmd_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user or not update.message:
        return

    telegram_id = user.id
    username = f"@{user.username}" if user.username else user.full_name
    first_name = user.first_name or user.full_name

    await _ensure_wallet_exists(telegram_id, username, first_name)

    url = f"{_api_base()}/api/wallet/by-telegram/{telegram_id}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status != 200:
                    await update.message.reply_text("לא הצלחתי להביא את פרטי הארנק כרגע.")
                    logger.error("wallet/by-telegram HTTP %s for %s", resp.status, telegram_id)
                    return
                data = await resp.json()
    except Exception as e:
        logger.error("Error calling wallet/by-telegram for %s: %s", telegram_id, e)
        await update.message.reply_text("אירעה שגיאה בזמן הבאת פרטי הארנק.")
        return

    bnb = data.get("bnb_address") or "לא מוגדרת"
    slh = data.get("slh_address") or "לא מוגדרת"
    bank = "קיימים" if data.get("bank_account_number") else "לא קיימים"

    text = (
        "🧾 תקציר הארנק שלך:\n\n"
        f"Telegram ID: {telegram_id}\n"
        f"BNB address: {bnb}\n"
        f"SLH address: {slh}\n"
        f"פרטי בנק: {bank}\n\n"
        "לפתיחת הצעת מכירה:\n"
        "/sell <כמות_SLH> <מחיר_BNB_ליחידה>\n"
        "לדוגמה: /sell 10 0.01"
    )

    await update.message.reply_text(text)
    logger.info("BOT /wallet from %s(%s)", username, telegram_id)


async def cmd_balances(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user or not update.message:
        return

    telegram_id = user.id
    username = f"@{user.username}" if user.username else user.full_name
    first_name = user.first_name or user.full_name

    await _ensure_wallet_exists(telegram_id, username, first_name)

    url = f"{_api_base()}/api/wallet/{telegram_id}/balances"

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
        await update.message.reply_text("אירעה שגיאה בזמן הבאת היתרות.")
        return

    if not data.get("success", False):
        await update.message.reply_text("לא קיימות כתובות רשומות לארנק שלך. עדכן כתובת BNB/SLH ואז נסה שוב.")
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


async def cmd_bank(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    כרגע: מסביר שהוספת פרטי בנק תתבצע מול האדמינים / דרך האתר.
    אפשר להרחיב בהמשך ל-API מלא.
    """
    if not update.message:
        return

    text = (
        "🏦 פרטי בנק לקבלת תשלומים:\n\n"
        "בשלב זה, עדכון פרטי הבנק נעשה מול צוות הקהילה.\n"
        "ניתן לשלוח צילום צ'ק / פרטי חשבון בקבוצת התמיכה או ישירות למנהל.\n\n"
        "בהמשך נוסיף אפשרות לעדכון ישיר דרך המערכת."
    )
    await update.message.reply_text(text)


async def cmd_sell(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /sell <amount> <price_bnb>
    לדוגמה: /sell 10 0.01
    """
    user = update.effective_user
    if not user or not update.message:
        return

    telegram_id = user.id
    username = f"@{user.username}" if user.username else user.full_name
    first_name = user.first_name or user.full_name

    await _ensure_wallet_exists(telegram_id, username, first_name)

    if len(context.args) != 2:
        await update.message.reply_text("שימוש: /sell <כמות_SLH> <מחיר_BNB_ליחידה>\nלדוגמה: /sell 10 0.01")
        return

    try:
        amount = float(context.args[0])
        price_bnb = float(context.args[1])
    except ValueError:
        await update.message.reply_text("הכמות והמחיר חייבים להיות מספרים.\nלדוגמה: /sell 10 0.01")
        return

    if amount <= 0 or price_bnb <= 0:
        await update.message.reply_text("הכמות והמחיר חייבים להיות חיוביים.")
        return

    url = f"{_api_base()}/api/trade/create-offer"
    params = {
        "telegram_id": str(telegram_id),
        "token_symbol": "SLH",
        "amount": amount,
        "price_bnb": price_bnb,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params=params, timeout=10) as resp:
                if resp.status != 200:
                    txt = await resp.text()
                    logger.error("create-offer HTTP %s: %s", resp.status, txt)
                    await update.message.reply_text("לא הצלחתי לפתוח הצעת מכירה כרגע.")
                    return
                data = await resp.json()
    except Exception as e:
        logger.error("Error calling create-offer: %s", e)
        await update.message.reply_text("אירעה שגיאה בפתיחת הצעת המכירה.")
        return

    offer_id = data.get("id")
    amount = data.get("amount")
    price = data.get("price_bnb")

    text = (
        "✅ נפתחה עבורך הצעת מכירה בשוק הקהילתי:\n\n"
        f"#{offer_id} – {amount} SLH @ {price} BNB ליחידה\n\n"
        "ניתן לראות את כל ההצעות עם /market"
    )
    await update.message.reply_text(text)
    logger.info("BOT /sell by %s(%s): %s SLH @ %s", username, telegram_id, amount, price_bnb)


async def cmd_market(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    url = f"{_api_base()}/api/trade/offers"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status != 200:
                    txt = await resp.text()
                    logger.error("offers HTTP %s: %s", resp.status, txt)
                    await update.message.reply_text("לא הצלחתי להביא את רשימת ההצעות.")
                    return
                offers = await resp.json()
    except Exception as e:
        logger.error("Error calling trade/offers: %s", e)
        await update.message.reply_text("אירעה שגיאה בהבאת ההצעות מהשוק.")
        return

    if not offers:
        await update.message.reply_text("אין עדיין הצעות בשוק. תהיה הראשון לפתוח הצעת מכירה עם /sell ✅")
        return

    lines = ["📈 שוק SLH הקהילתי:\n"]
    for o in offers[:20]:
        oid = o.get("id")
        token = o.get("token_symbol")
        amount = o.get("amount")
        price = o.get("price_bnb")
        seller = o.get("telegram_id")
        lines.append(f"#{oid} – {amount} {token} @ {price} BNB (מוכר: {seller})")

    text = "\n".join(lines)
    await update.message.reply_text(text)


# ===== FastAPI webhook =====

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
