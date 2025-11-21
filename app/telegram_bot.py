import json
import logging
import aiohttp
from typing import Optional
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

router = APIRouter(tags=["telegram"])

_application: Optional[Application] = None

async def _build_application() -> Application:
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")

    try:
        app = (
            ApplicationBuilder()
            .token(settings.telegram_bot_token)
            .concurrent_updates(True)
            .build()
        )

        app.add_handler(CommandHandler("start", cmd_start))
        app.add_handler(CommandHandler("wallet", cmd_wallet))
        app.add_handler(CommandHandler("balances", cmd_balances))
        app.add_handler(CommandHandler("bank", cmd_bank))  # ✅ פקודה חדשה
        
        return app
    except Exception as e:
        logger.error("Failed to build Telegram application: %s", e)
        raise

async def get_application() -> Application:
    global _application
    if _application is None:
        _application = await _build_application()
        await _application.initialize()
    return _application

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        user = update.effective_user
        if not user:
            return
            
        logger.info("BOT /start from @%s(%s)", user.username, user.id)

        base = settings.base_url or "https://thin-charlot-osifungar-d382d3c9.koyeb.app"

        text = (
            f"שלום @{user.username or user.id}! 🌐\n\n"
            "ברוך הבא ל-SLH Wallet 2.0 - ארנק הקהילה המלא! 🚀\n\n"
            "🪙 **פיצ'רים זמינים:**\n"
            "• /wallet - ניהול כתובות ארנק ופרטים\n"
            "• /balances - צפייה ביתרות\n"
            "• /bank - הוספת פרטי בנק\n"
            "• מסחר P2P (בקרוב)\n\n"
            "פתיחת ארנק / עדכון פרטים:\n"
            f"➡️ {base}/wallet\n"
            f"לקבוצת הקהילה: {settings.community_link}"
        )

        await update.effective_chat.send_message(text)
    except Exception as e:
        logger.error("Error in /start command: %s", e)

async def cmd_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        user = update.effective_user
        if not user:
            return
            
        logger.info("BOT /wallet from @%s(%s)", user.username, user.id)

        base = settings.base_url or "https://thin-charlot-osifungar-d382d3c9.koyeb.app"
        url = (
            f"{base}/wallet"
            f"?telegram_id={user.id}"
            f"&username={user.username or ''}"
            f"&first_name={user.first_name or ''}"
        )

        text = (
            "📲 **ניהול ארנק מלא:**\n\n"
            "להגדרת ארנק / עדכון פרטים:\n"
            f"➡️ {url}\n\n"
            "**מה ניתן לעשות:**\n"
            "• חיבור MetaMask אוטומטי\n"
            "• הגדרת כתובות BNB/SLH\n"
            "• הוספת פרטי בנק\n"
            "• העלאת אישורי העברה\n\n"
            "לאחר ההגדרה, השתמש ב:\n"
            "• /balances - לצפייה ביתרות\n"
            "• /bank - לניהול פרטי בנק"
        )

        await update.effective_chat.send_message(text)
    except Exception as e:
        logger.error("Error in /wallet command: %s", e)

async def cmd_bank(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """✅ פקודה חדשה - ניהול פרטי בנק"""
    try:
        user = update.effective_user
        if not user:
            return

        logger.info("BOT /bank from @%s(%s)", user.username, user.id)

        base = settings.base_url or "https://thin-charlot-osifungar-d382d3c9.koyeb.app"
        url = f"{base}/wallet?telegram_id={user.id}"

        text = (
            "🏦 **ניהול פרטי בנק:**\n\n"
            "להוספת/עדכון פרטי בנק להעברות:\n"
            f"➡️ {url}\n\n"
            "**ניתן להוסיף:**\n"
            "• שם הבנק וסניף\n"
            "• מספר חשבון\n"
            "• העלאת אישורי העברה\n\n"
            "הפרטים ישמשו לקבלת תשלומים\n"
            "בעבור המטבעות שלך."
        )

        await update.effective_chat.send_message(text)
    except Exception as e:
        logger.error("Error in /bank command: %s", e)

async def cmd_balances(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        user = update.effective_user
        if not user:
            return

        logger.info("BOT /balances from @%s(%s)", user.username, user.id)

        base_url = settings.base_url or "https://thin-charlot-osifungar-d382d3c9.koyeb.app"
        api_url = f"{base_url}/api/wallet/{user.id}/balances"

        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    if data.get('success', False):
                        text = (
                            "🏦 **יתרות הארנק שלך:**\n\n"
                            f"💎 BNB: `{data['bnb_balance']:.6f}`\n"
                            f"🪙 SLH: `{data['slh_balance']:.2f}`\n\n"
                            f"📍 כתובת BNB: `{data['bnb_address']}`\n"
                            f"📍 כתובת SLH: `{data['slh_address']}`"
                        )
                    else:
                        text = (
                            "❌ **לא נמצא ארנק**\n\n"
                            "עליך לרשום ארנק תחילה:\n"
                            "השתמש ב-/wallet כדי להירשם"
                        )
                else:
                    text = (
                        "❌ **לא נמצא ארנק**\n\n"
                        "עליך לרשום ארנק תחילה:\n"
                        "השתמש ב-/wallet כדי להירשם"
                    )

        await update.effective_chat.send_message(text, parse_mode='Markdown')
    except Exception as e:
        logger.error("Error in /balances command: %s", e)
        await update.effective_chat.send_message("❌ אירעה שגיאה בשליפת היתרות. נסה שוב מאוחר יותר.")

@router.post("/telegram/webhook")
async def telegram_webhook(
    request: Request,
) -> dict:
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
