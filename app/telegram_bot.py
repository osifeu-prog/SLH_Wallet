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
from .database import SessionLocal
from . import models

logger = logging.getLogger("slh_wallet.bot")

router = APIRouter(tags=["telegram"])

_application: Optional[Application] = None


async def _build_application() -> Application:
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")

    app = (
        ApplicationBuilder()
        .token(settings.telegram_bot_token)
        .concurrent_updates(True)
        .build()
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("wallet", cmd_wallet))
    app.add_handler(CommandHandler("set_bnb", cmd_set_bnb))

    return app


async def get_application() -> Application:
    global _application
    if _application is None:
        _application = await _build_application()
        await _application.initialize()
    return _application


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Welcome message: explains SLH community wallet on BNB Smart Chain."""
    user = update.effective_user
    if not user:
        return

    logger.info("BOT /start from @%s(%s)", user.username, user.id)

    base = settings.base_url
    token_address = settings.slh_token_address

    lines = [
        f"שלום {('@' + user.username) if user.username else user.full_name}! 🌐",
        "",
        "ברוך הבא ל-SLH Community Wallet – ארנק קהילתי פשוט על רשת BNB Smart Chain.",
        "",
        "🔑 *ללא סיסמאות – רק טלגרם + ארנק BNB שלך.*",
        "",
        "ℹ️ איך זה עובד:",
        "1. פותחים כרטיס משתמש דרך הפקודה /wallet",
        "2. מוסיפים את כתובת ארנק ה-BNB שלך עם הפקודה:",
        "   /set_bnb <כתובת_BNB שלך>",
        "3. מעכשיו אתה יכול לשתף את כרטיס המשתמש שלך,",
        "   והחברים יכולים לשלוח לך BNB או SLH ישירות לארנק.",
        "",
        "🪙 פרטי טוקן SLH (על BNB Smart Chain):",
        f"• Contract: {token_address}",
        "• Network: BNB Smart Chain (ChainID 56)",
        "• RPC: https://bsc-dataseed.binance.org/",
        "• Explorer: https://bscscan.com/token/" + token_address,
        "",
        "💡 מסחר ב-SLH מתבצע דרך כל ארנק שתומך ב-BNB (לדוגמה MetaMask),",
        "   או דרך כל DEX שתומך ב-BNB Smart Chain (כמו PancakeSwap).",
        "",
        "כדי להגדיר את הכרטיס שלך במערכת, השתמש בפקודה /wallet."
    ]

    # שליחת טקסט פשוט ללא Markdown כדי להימנע מבעיות פירסינג
    await update.effective_chat.send_message("\n".join(lines))


async def cmd_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Create/ensure a wallet row for this Telegram user and show personal hub link."""
    user = update.effective_user
    if not user:
        return

    logger.info("BOT /wallet from @%s(%s)", user.username, user.id)

    session = SessionLocal()
    try:
        wallet = session.get(models.Wallet, str(user.id))
        created = False
        if not wallet:
            wallet = models.Wallet(
                telegram_id=str(user.id),
                username=user.username or "",
                first_name=user.first_name or "",
                last_name=user.last_name or "",
            )
            session.add(wallet)
            created = True
        else:
            # עדכון בסיסי של פרטים
            wallet.username = user.username or wallet.username
            wallet.first_name = user.first_name or wallet.first_name
            wallet.last_name = user.last_name or wallet.last_name

        session.commit()
    finally:
        session.close()

    base = settings.base_url
    hub_url = f"{base}/u/{user.id}"

    lines = [
        "📲 כרטיס ה-SLH הקהילתי שלך מוכן במערכת.",
        "",
        "זהותך במערכת מוגדרת ע"י:",
        "• Telegram ID שלך",
        "• כתובת ארנק BNB שלך (אותה תזין בקרוב)",
        "",
        "כדי להגדיר את כתובת ארנק ה-BNB שלך:",
        "1. פתח את ארנק ה-BNB שלך (לדוגמה MetaMask על רשת BNB Smart Chain)",
        "2. העתק את הכתובת שלך (שמתחילה ב-0x)",
        "3. שלח את הפקודה:",
        "   /set_bnb <כתובת_BNB שלך>",
        "",
        "🔗 האזור האישי שלך ברשת SLH:",
        f"{hub_url}",
        "",
        "את הקישור הזה אפשר לשתף עם חברים כדי שיראו את הפרטים שלך וישלחו SLH/BNB ישירות לארנק שלך.",
    ]

    await update.effective_chat.send_message("\n".join(lines))


async def cmd_set_bnb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Update the user's BNB (BSC) address in the DB.

    שימוש: /set_bnb <כתובת_BNB>
    """
    user = update.effective_user
    if not user:
        return

    if not context.args:
        await update.effective_chat.send_message("שימוש: /set_bnb <כתובת_BNB שלך על רשת BNB Smart Chain>")
        return

    address = context.args[0].strip()

    # ולידציה בסיסית בלבד
    if not (address.startswith("0x") and len(address) >= 30):
        await update.effective_chat.send_message("הכתובת לא נראית כמו כתובת BNB תקינה. ודא שהעתקת נכון (0x...)")
        return

    session = SessionLocal()
    try:
        wallet = session.get(models.Wallet, str(user.id))
        if not wallet:
            # אם משום מה אין רשומה – ניצור אחת מינימלית
            wallet = models.Wallet(
                telegram_id=str(user.id),
                username=user.username or "",
                first_name=user.first_name or "",
                last_name=user.last_name or "",
                bnb_address=address,
            )
            session.add(wallet)
        else:
            wallet.bnb_address = address

        session.commit()
    finally:
        session.close()

    await update.effective_chat.send_message("✅ כתובת ארנק ה-BNB שלך עודכנה בהצלחה במערכת.")


@router.post("/telegram/webhook")
async def telegram_webhook(request: Request) -> dict:
    """Webhook entry from Telegram -> forwards updates to python-telegram-bot app."""
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
    except Exception as e:  # noqa: BLE001
        logger.error("Error processing webhook: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")
