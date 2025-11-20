
from typing import Optional
from fastapi import APIRouter, Request
from .config import get_settings
from .logging_utils import log_event

from telegram import Update
from telegram.ext import Application, ApplicationBuilder, CommandHandler, ContextTypes

settings = get_settings()

router = APIRouter()

_bot_app: Optional[Application] = None


def get_bot_application() -> Optional[Application]:
    global _bot_app
    if _bot_app is None and settings.TELEGRAM_BOT_TOKEN:
        _bot_app = (
            ApplicationBuilder()
            .token(settings.TELEGRAM_BOT_TOKEN)
            .concurrent_updates(True)
            .build()
        )

        _bot_app.add_handler(CommandHandler("start", cmd_start))
        _bot_app.add_handler(CommandHandler("wallet", cmd_wallet))
        _bot_app.add_handler(CommandHandler("debug_admin", cmd_debug_admin))
        _bot_app.add_handler(CommandHandler("chatid", cmd_chatid))

    return _bot_app


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await log_event("bot", f"/start from @{user.username}({user.id})")

    base_url = settings.BASE_URL or "https://example.com"
    text = (
        f"שלום @{user.username}! \U0001F310\n\n"
        "ברוך הבא ל-SLH Wallet 2.0.\n\n"
        "כאן נרכז בהמשך:\n"
        "• ארנק BNB/SLH אישי\n"
        "• כתובת SLH מזוהה למערכת\n"
        "• חיבור לכלי המסחר והקהילה.\n\n"
        f"פתיחת ארנק / התחברות:\n➡️ {base_url}/\n"
    )
    if settings.COMMUNITY_LINK:
        text += f"לקבוצת הקהילה: {settings.COMMUNITY_LINK}"

    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)


async def cmd_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await log_event("bot", f"/wallet from @{user.username}({user.id})")
    base_url = settings.BASE_URL or "https://example.com"
    url = f"{base_url}/#wallet"
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"להגדרת ארנק / עדכון פרטים:\n➡️ {url}",
    )


async def cmd_debug_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat

    env_admin_chat = settings.ADMIN_LOG_CHAT_ID
    text = (
        "🔍 Debug Admin\n\n"
        f"chat_id נוכחי: {chat.id}\n"
        f"ADMIN_LOG_CHAT_ID מה-ENV: {env_admin_chat}\n"
    )

    if env_admin_chat and env_admin_chat != chat.id:
        text += "\nℹ️ אתה לא בקבוצת הלוגים. אשלח לשם הודעת בדיקה."

        try:
            await context.bot.send_message(
                chat_id=env_admin_chat,
                text=f"[ADMIN_LOG_TEST] /debug_admin מקבוצת {chat.id} על ידי @{user.username}({user.id})",
            )
        except Exception as e:
            await log_event("bot", f"Failed to send test log to ADMIN_LOG_CHAT_ID: {e}")

    await context.bot.send_message(chat_id=chat.id, text=text)


async def cmd_chatid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    await context.bot.send_message(
        chat_id=chat.id,
        text=f"🔑 chat_id הנוכחי: {chat.id}",
    )


@router.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    app = get_bot_application()
    if not app:
        await log_event("bot", "Webhook called but TELEGRAM_BOT_TOKEN is not set")
        return {"status": "no-bot"}

    data = await request.json()
    update = Update.de_json(data, app.bot)
    await app.initialize()
    await app.process_update(update)
    return {"ok": True}
