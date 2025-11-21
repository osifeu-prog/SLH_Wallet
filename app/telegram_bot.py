import json
import logging
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
        
        return app
    except Exception as e:
        logger.error("Failed to build Telegram application: %s", e)
        raise


async def get_application() -> Application:
    global _application
    if _application is None:
        _application = await _build_application()
        await _application.initialize()
        # ✅ לא מפעילים את polling - משתמשים ב-webhook בלבד
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
            "ברוך הבא ל-SLH Wallet 2.0.\n\n"
            "כאן נרכז בהמשך:\n"
            "• ארנק BNB/SLH אישי\n"
            "• כתובת SLH מזוהה למערכת\n"
            "• חיבור לכלי המסחר והקהילה.\n\n"
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

        text = "להגדרת ארנק / עדכון פרטים:\n" f"➡️ {url}"

        await update.effective_chat.send_message(text)
    except Exception as e:
        logger.error("Error in /wallet command: %s", e)


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
