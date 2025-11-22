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
from .database import SessionLocal
from . import models

logger = logging.getLogger("slh_wallet.bot")

router = APIRouter(tags=["telegram"])

_application: Optional[Application] = None


async def _build_application() -> Application:
    """Create and configure the telegram Application instance."""
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
        app.add_handler(CommandHandler("bank", cmd_bank))
        app.add_handler(CommandHandler("set_bnb", cmd_set_bnb))
        app.add_handler(CommandHandler("set_ton", cmd_set_ton))

        return app
    except Exception as e:  # noqa: BLE001
        logger.error("Failed to build Telegram application: %s", e)
        raise


async def get_application() -> Application:
    """Return a singleton Application instance (created lazily)."""
    global _application
    if _application is None:
        _application = await _build_application()
        await _application.initialize()
    return _application


def _ensure_wallet_sync(
    telegram_id: str,
    username: str = "",
    first_name: str = "",
    last_name: str = "",
) -> models.Wallet:
    """
    Create a minimal Wallet row for this telegram_id if it does not exist yet.
    This is synchronous and meant to be used from inside bot handlers.
    """
    session = SessionLocal()
    try:
        wallet = session.get(models.Wallet, telegram_id)
        if not wallet:
            wallet = models.Wallet(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
            )
            session.add(wallet)
            session.commit()
            session.refresh(wallet)
        return wallet
    finally:
        session.close()


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start – intro to the SLH wallet."""
    try:
        user = update.effective_user
        if not user:
            return

        logger.info("BOT /start from @%s(%s)", user.username, user.id)

        base = (
            settings.base_url
            or settings.frontend_api_base
            or "https://thin-charlot-osifungar-d382d3c9.koyeb.app"
        )

        text = (
            f"שלום @{user.username or user.id}! 🌐\n\n"
            "ברוך הבא ל-SLH Wallet 2.0 - ארנק הקהילה המלא! 🚀\n\n"
            "🪙 *פיצ'רים זמינים:*\n"
            "• /wallet - ניהול כתובות ארנק ופרטים\n"
            "• /balances - צפייה ביתרות\n"
            "• /bank - הוספת פרטי בנק\n"
            "• מסחר P2P (בקרוב)\n\n"
            "פתיחת ארנק / עדכון פרטים:\n"
            f"➡️ {base}/wallet\n"
            f"לקבוצת הקהילה: {settings.community_link}"
        )

        await update.effective_chat.send_message(text, parse_mode="Markdown")
    except Exception as e:  # noqa: BLE001
        logger.error("Error in /start command: %s", e)


async def cmd_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    נקודת הכניסה לניהול הארנק דרך הבוט.

    ✳ פותח/מעדכן רשומת Wallet בטבלה
    ✳ מציג למשתמש קישור לאזור האישי באתר (/u/{telegram_id})
    ✳ מסביר איך לעדכן כתובות BNB ו-TON
    """
    try:
        user = update.effective_user
        if not user:
            return

        logger.info("BOT /wallet from @%s(%s)", user.username, user.id)

        # מוודא שקיימת רשומת ארנק בסיסית
        _ensure_wallet_sync(
            telegram_id=str(user.id),
            username=user.username or "",
            first_name=user.first_name or "",
            last_name=user.last_name or "",
        )

        base = (
            settings.frontend_api_base
            or settings.base_url
            or "https://thin-charlot-osifungar-d382d3c9.koyeb.app"
        )
        hub_url = f"{base}/u/{user.id}"

        text = (
            "📲 *הארנק שלך במערכת SLH מוכן!*\n\n"
            "אנחנו לא שומרים סיסמאות ולא מבקשים רישום באתר.\n"
            "זהותך במערכת = Telegram + כתובות ארנק בלבד.\n\n"
            "🔐 *מה עכשיו?*\n"
            "1. שלח לי את כתובת ה־BNB שלך עם הפקודה:\n"
            "   `/set_bnb <כתובת_BNB>`\n"
            "2. שלח את כתובת ה־TON שלך עם הפקודה:\n"
            "   `/set_ton <כתובת_TON>`\n\n"
            "לאחר העדכון, האזור האישי שלך יציג תצוגה מלאה של הנכסים.\n\n"
            "🧾 *האזור האישי שלך בבורסה הקהילתית:*\n"
            f"➡️ {hub_url}\n\n"
            "כל פעולה רגישה (סטייקינג, ניהול בנק, משיכות) מתבצעת *רק כאן בבוט*."
        )

        await update.effective_chat.send_message(text, parse_mode="Markdown")
    except Exception as e:  # noqa: BLE001
        logger.error("Error in /wallet command: %s", e)


async def cmd_set_bnb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    עדכון כתובת BNB של המשתמש דרך הבוט.

    שימוש: /set_bnb <כתובת_BNB>
    """
    user = update.effective_user
    if not user:
        return

    if not context.args:
        await update.effective_chat.send_message("שימוש: /set_bnb <כתובת_BNB>")
        return

    address = context.args[0].strip()
    # ולידציה בסיסית
    if not address.startswith("0x") or len(address) < 30:
        await update.effective_chat.send_message(
            "הכתובת ששלחת לא נראית כמו כתובת BNB תקינה."
        )
        return

    session = SessionLocal()
    try:
        wallet = session.get(models.Wallet, str(user.id))
        if not wallet:
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

    await update.effective_chat.send_message(
        "✅ כתובת ה-BNB שלך עודכנה בהצלחה במערכת."
    )


async def cmd_set_ton(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    עדכון כתובת TON של המשתמש דרך הבוט.

    שימוש: /set_ton <כתובת_TON>
    """
    user = update.effective_user
    if not user:
        return

    if not context.args:
        await update.effective_chat.send_message("שימוש: /set_ton <כתובת_TON>")
        return

    address = " ".join(context.args).strip()

    session = SessionLocal()
    try:
        wallet = session.get(models.Wallet, str(user.id))
        if not wallet:
            wallet = models.Wallet(
                telegram_id=str(user.id),
                username=user.username or "",
                first_name=user.first_name or "",
                last_name=user.last_name or "",
                slh_ton_address=address,
            )
            session.add(wallet)
        else:
            wallet.slh_ton_address = address
        session.commit()
    finally:
        session.close()

    await update.effective_chat.send_message(
        "✅ כתובת ה-TON שלך עודכנה בהצלחה במערכת."
    )


async def cmd_bank(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """קישור לניהול פרטי בנק (כרגע דרך טופס באתר)."""
    try:
        user = update.effective_user
        if not user:
            return

        logger.info("BOT /bank from @%s(%s)", user.username, user.id)

        base = (
            settings.base_url
            or settings.frontend_api_base
            or "https://thin-charlot-osifungar-d382d3c9.koyeb.app"
        )
        url = f"{base}/wallet?telegram_id={user.id}"

        text = (
            "🏦 *ניהול פרטי בנק:*\n\n"
            "להוספת/עדכון פרטי בנק להעברות:\n"
            f"➡️ {url}\n\n"
            "*ניתן להוסיף:*\n"
            "• שם הבנק וסניף\n"
            "• מספר חשבון\n"
            "• העלאת אישורי העברה\n\n"
            "הפרטים ישמשו לקבלת תשלומים בעבור המטבעות שלך."
        )

        await update.effective_chat.send_message(text, parse_mode="Markdown")
    except Exception as e:  # noqa: BLE001
        logger.error("Error in /bank command: %s", e)


async def cmd_balances(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """הצגת יתרות (on-chain + פנימי) למשתמש."""
    try:
        user = update.effective_user
        if not user:
            return

        logger.info("BOT /balances from @%s(%s)", user.username, user.id)

        base_url = (
            settings.base_url
            or settings.frontend_api_base
            or "https://thin-charlot-osifungar-d382d3c9.koyeb.app"
        )
        api_url = f"{base_url}/api/wallet/{user.id}/balances"

        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as resp:
                if resp.status == 200:
                    data = await resp.json()

                    if data.get("success", False):
                        text = (
                            "🏦 *יתרות הארנק שלך:*\n\n"
                            f"💎 BNB: `{data['bnb_balance']:.6f}`\n"
                            f"🪙 SLH: `{data['slh_balance']:.2f}`\n\n"
                            f"📍 כתובת BNB: `{data['bnb_address']}`\n"
                            f"📍 כתובת SLH: `{data['slh_address']}`"
                        )
                    else:
                        text = (
                            "❌ *לא נמצא ארנק*\n\n"
                            "עליך לרשום ארנק תחילה:\n"
                            "השתמש ב-/wallet כדי להירשם"
                        )
                else:
                    text = (
                        "❌ *לא נמצא ארנק*\n\n"
                        "עליך לרשום ארנק תחילה:\n"
                        "השתמש ב-/wallet כדי להירשם"
                    )

        await update.effective_chat.send_message(text, parse_mode="Markdown")
    except Exception as e:  # noqa: BLE001
        logger.error("Error in /balances command: %s", e)
        await update.effective_chat.send_message(
            "❌ אירעה שגיאה בשליפת היתרות. נסה שוב מאוחר יותר."
        )


@router.post("/telegram/webhook")
async def telegram_webhook(request: Request) -> dict:
    """FastAPI entrypoint for Telegram webhook."""
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
