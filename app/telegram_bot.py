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
from .blockchain_service import blockchain_service
from .ton_service import ton_service

logger = logging.getLogger("slh_wallet.bot")

router = APIRouter(prefix="/telegram", tags=["telegram"])

_application: Optional[Application] = None


async def _ensure_wallet(telegram_id: str, username: str = "", first_name: str = "", last_name: str = "") -> models.Wallet:
    db = SessionLocal()
    try:
        wallet = db.get(models.Wallet, telegram_id)
        created = False
        if wallet is None:
            wallet = models.Wallet(
                telegram_id=telegram_id,
                username=username or None,
                first_name=first_name or None,
                last_name=last_name or None,
            )
            db.add(wallet)
            created = True
        else:
            if username:
                wallet.username = username
            if first_name:
                wallet.first_name = first_name
            if last_name:
                wallet.last_name = last_name
        db.commit()
        db.refresh(wallet)
        if created:
            logger.info("Created wallet for telegram_id=%s", telegram_id)
        return wallet
    finally:
        db.close()


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user:
        return

    telegram_id = str(user.id)
    username = user.username or ""
    first_name = user.first_name or ""
    last_name = user.last_name or ""

    await _ensure_wallet(telegram_id, username, first_name, last_name)

    text_lines = [
        "ברוך הבא ל-SLH Wallet 🚀",
        "",
        "כאן אתה מנהל את הארנק הקהילתי שלך, מחבר כתובות BNB/SLH/TON ומנהל מסחר קהילתי.",
        "",
        "פקודות זמינות:",
        "/wallet - פרטי הארנק שלך",
        "/balances - הצגת יתרות מרשתות BNB / SLH_BNB / SLH_TON",
        "/link_bnb <address> - קישור כתובת BNB/SLH_BNB",
        "/link_slh <address> - קישור כתובת SLH_BNB (אם שונה)",
        "/link_slh_ton <address> - קישור כתובת SLH_TON (עתידי)",
        "/sell <amount> <price_bnb> - פתיחת הצעת מכירה",
        "/market - צפייה בשוק הקהילתי",
    ]
    await update.effective_chat.send_message("\n".join(text_lines))


async def cmd_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user:
        return
    telegram_id = str(user.id)

    db = SessionLocal()
    try:
        wallet = db.get(models.Wallet, telegram_id)
        if not wallet:
            await update.effective_chat.send_message("לא נמצא ארנק. השתמש ב-/start כדי לפתוח אחד.")
            return

        lines = [
            "🧾 פרטי הארנק הקהילתי שלך:",
            f"Telegram ID: {wallet.telegram_id}",
        ]
        if wallet.username:
            lines.append(f"Username: @{wallet.username}")
        lines.extend(
            [
                "",
                f"BNB / SLH_BNB address: {wallet.bnb_address or wallet.slh_address or 'לא הוגדר'}",
                f"SLH_BNB address (נפרד): {wallet.slh_address or 'לא הוגדר'}",
                f"SLH_TON address: {wallet.slh_ton_address or 'לא הוגדר'}",
            ]
        )
        if wallet.bank_account_number:
            lines.append("")
            lines.append("🏦 פרטי בנק (לא חובה לשימוש במערכת):")
            lines.append(f"מספר חשבון: {wallet.bank_account_number}")
            if wallet.bank_account_name:
                lines.append(f"שם בעל החשבון: {wallet.bank_account_name}")

        await update.effective_chat.send_message("\n".join(lines))
    finally:
        db.close()


async def cmd_balances(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user:
        return
    telegram_id = str(user.id)

    db = SessionLocal()
    try:
        wallet = db.get(models.Wallet, telegram_id)
        if not wallet:
            await update.effective_chat.send_message("לא נמצא ארנק. השתמש ב-/start כדי לפתוח אחד.")
            return

        bnb_address = wallet.bnb_address or wallet.slh_address
        slh_address = wallet.slh_address or wallet.bnb_address

        chain_balances = await blockchain_service.get_balances(bnb_address or "", slh_address or "")
        slh_ton_balance = 0.0
        if wallet.slh_ton_address:
            slh_ton_balance = await ton_service.get_slh_ton_balance(wallet.slh_ton_address)

        text_lines = [
            "📊 יתרות הארנק שלך:",
            f"BNB: {chain_balances.get('bnb', 0.0):.6f}",
            f"SLH_BNB: {chain_balances.get('slh', 0.0):.4f}",
            f"SLH_TON: {slh_ton_balance:.4f} (1 SLH_TON = {settings.slh_ton_factor:.0f} SLH_BNB לוגיים)",
        ]
        await update.effective_chat.send_message("\n".join(text_lines))
    finally:
        db.close()


async def cmd_link_bnb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user:
        return
    telegram_id = str(user.id)

    if not context.args:
        await update.effective_chat.send_message("שימוש: /link_bnb <כתובת>")
        return

    address = context.args[0].strip()

    db = SessionLocal()
    try:
        wallet = await _ensure_wallet(telegram_id)
        wallet.bnb_address = address
        db = SessionLocal()
        db.merge(wallet)
        db.commit()
        await update.effective_chat.send_message(f"✅ כתובת BNB עודכנה:\n{address}")
    finally:
        db.close()


async def cmd_link_slh(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user:
        return
    telegram_id = str(user.id)

    if not context.args:
        await update.effective_chat.send_message("שימוש: /link_slh <כתובת SLH_BNB>")
        return

    address = context.args[0].strip()

    db = SessionLocal()
    try:
        wallet = await _ensure_wallet(telegram_id)
        wallet.slh_address = address
        db = SessionLocal()
        db.merge(wallet)
        db.commit()
        await update.effective_chat.send_message(f"✅ כתובת SLH_BNB עודכנה:\n{address}")
    finally:
        db.close()


async def cmd_link_slh_ton(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user:
        return
    telegram_id = str(user.id)

    if not context.args:
        await update.effective_chat.send_message("שימוש: /link_slh_ton <כתובת SLH_TON>")
        return

    address = context.args[0].strip()

    db = SessionLocal()
    try:
        wallet = await _ensure_wallet(telegram_id)
        wallet.slh_ton_address = address
        db = SessionLocal()
        db.merge(wallet)
        db.commit()
        await update.effective_chat.send_message(f"✅ כתובת SLH_TON עודכנה:\n{address}")
    finally:
        db.close()


async def cmd_sell(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user:
        return
    telegram_id = str(user.id)

    if len(context.args) < 2:
        await update.effective_chat.send_message("שימוש: /sell <כמות SLH_BNB> <מחיר ליחידה ב-BNB>")
        return

    try:
        amount = float(context.args[0])
        price_bnb = float(context.args[1])
    except ValueError:
        await update.effective_chat.send_message("ערכים לא תקינים. דוגמה: /sell 10 0.01")
        return

    if amount <= 0 or price_bnb <= 0:
        await update.effective_chat.send_message("כמות ומחיר חייבים להיות חיוביים.")
        return

    db = SessionLocal()
    try:
        wallet = db.get(models.Wallet, telegram_id)
        if not wallet:
            await update.effective_chat.send_message("לא נמצא ארנק. השתמש ב-/start קודם.")
            return

        offer = models.TradeOffer(
            seller_telegram_id=telegram_id,
            token_symbol="SLH_BNB",
            amount=amount,
            price_bnb=price_bnb,
            status="ACTIVE",
        )
        db.add(offer)
        db.commit()
        db.refresh(offer)

        await update.effective_chat.send_message(
            f"✅ נפתחה הצעת מכירה #{offer.id}:\n"
            f"מוכר: @{wallet.username or telegram_id}\n"
            f"כמות: {amount} SLH_BNB\n"
            f"מחיר ליחידה: {price_bnb} BNB"
        )
    finally:
        db.close()


async def cmd_market(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user:
        return

    db = SessionLocal()
    try:
        offers = (
            db.query(models.TradeOffer)
            .filter(models.TradeOffer.status == "ACTIVE")
            .order_by(models.TradeOffer.created_at.desc())
            .limit(20)
            .all()
        )
        if not offers:
            await update.effective_chat.send_message("אין עדיין הצעות פעילות בשוק הקהילתי.")
            return

        lines = ["📈 שוק SLH הקהילתי – 20 ההצעות האחרונות:", ""]
        for offer in offers:
            seller = db.get(models.Wallet, offer.seller_telegram_id)
            if seller and seller.username:
                seller_name = f"@{seller.username}"
            else:
                seller_name = offer.seller_telegram_id
            lines.append(
                f"#{offer.id} | {offer.amount} {offer.token_symbol} @ {offer.price_bnb} BNB  (מוכר: {seller_name})"
            )

        await update.effective_chat.send_message("\n".join(lines))
    finally:
        db.close()


async def get_application() -> Application:
    global _application
    if _application is None:
        if not settings.telegram_bot_token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")

        app = ApplicationBuilder().token(settings.telegram_bot_token).build()

        app.add_handler(CommandHandler("start", cmd_start))
        app.add_handler(CommandHandler("wallet", cmd_wallet))
        app.add_handler(CommandHandler("balances", cmd_balances))
        app.add_handler(CommandHandler("link_bnb", cmd_link_bnb))
        app.add_handler(CommandHandler("link_slh", cmd_link_slh))
        app.add_handler(CommandHandler("link_slh_ton", cmd_link_slh_ton))
        app.add_handler(CommandHandler("sell", cmd_sell))
        app.add_handler(CommandHandler("market", cmd_market))

        await app.initialize()
        await app.start()

        _application = app
        logger.info("Telegram Application initialized successfully")

    return _application


@router.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        body = await request.body()
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
