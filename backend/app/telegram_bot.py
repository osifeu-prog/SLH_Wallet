
from typing import Any, Dict
from fastapi import APIRouter
from .config import get_settings
from .logger import logger

router = APIRouter(tags=["Telegram"], include_in_schema=False)
settings = get_settings()

@router.post("/telegram/webhook")
async def telegram_webhook(update: Dict[str, Any]):
    """Very small handler that reacts to /start, /wallet, /debug_admin, /chatid."""
    try:
        message = update.get("message") or update.get("edited_message") or {}
        text = (message.get("text") or "").strip()
        chat = message.get("chat") or {}
        chat_id = chat.get("id")
        chat_type = chat.get("type")
        from_user = message.get("from") or {}
        username = from_user.get("username")
        first_name = from_user.get("first_name")
        logger.info(f"[BOT] chat_id={chat_id}, chat_type={chat_type}, user=@{username} text={text!r}")

        # Basic command parsing
        if text.startswith("/start"):
            # We don't reply directly here – the real bot logic can live in a separate process.
            logger.info("[BOT] /start received")
        elif text.startswith("/wallet"):
            logger.info("[BOT] /wallet received")
        elif text.startswith("/debug_admin"):
            logger.info(f"[BOT] /debug_admin from @{username} ({chat_id})")
        elif text.startswith("/chatid"):
            logger.info(f"[BOT] /chatid from @{username} ({chat_id})")

    except Exception as e:
        logger.exception(f"Error handling telegram update: {e}")
    return {"ok": True}
