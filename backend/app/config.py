
import os
from functools import lru_cache
from pydantic import BaseModel


class Settings(BaseModel):
    ENV: str = os.getenv("ENV", "production")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Core service
    BASE_URL: str = os.getenv("BASE_URL", "").rstrip("/") or ""
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me")

    # Database
    DATABASE_URL: str | None = os.getenv("DATABASE_URL")

    # Blockchain
    BSC_RPC_URL: str = os.getenv("BSC_RPC_URL", "https://bsc-dataseed.binance.org/")

    # Telegram
    TELEGRAM_BOT_TOKEN: str | None = os.getenv("TELEGRAM_BOT_TOKEN")
    ADMIN_LOG_CHAT_ID: int | None = (
        int(os.getenv("ADMIN_LOG_CHAT_ID")) if os.getenv("ADMIN_LOG_CHAT_ID") else None
    )
    ADMIN_USERNAMES: str | None = os.getenv("ADMIN_USERNAMES")

    # Frontend/meta
    FRONTEND_BOT_URL: str | None = os.getenv("FRONTEND_BOT_URL")
    COMMUNITY_LINK: str | None = os.getenv("COMMUNITY_LINK")


@lru_cache
def get_settings() -> Settings:
    return Settings()
