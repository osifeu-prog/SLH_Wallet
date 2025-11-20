
import os
from functools import lru_cache

class Settings:
    PROJECT_NAME: str = "SLH_Wallet_2.0"
    ENV: str = os.getenv("ENV", "development")
    BASE_URL: str | None = os.getenv("BASE_URL")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change_me")
    DATABASE_URL: str | None = os.getenv("DATABASE_URL")
    BSC_RPC_URL: str | None = os.getenv("BSC_RPC_URL", "https://bsc-dataseed.binance.org/")
    TELEGRAM_BOT_TOKEN: str | None = os.getenv("TELEGRAM_BOT_TOKEN")
    ADMIN_LOG_CHAT_ID: int | None = int(os.getenv("ADMIN_LOG_CHAT_ID")) if os.getenv("ADMIN_LOG_CHAT_ID") else None
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    FRONTEND_BOT_URL: str | None = os.getenv("FRONTEND_BOT_URL")
    COMMUNITY_LINK: str | None = os.getenv("COMMUNITY_LINK")
    PAYMENT_METHODS: str | None = os.getenv("PAYMENT_METHODS")
    BUY_MY_SHOP_API: str | None = os.getenv("BUY_MY_SHOP_API")
    BUY_MY_SHOP_SECRET: str | None = os.getenv("BUY_MY_SHOP_SECRET")

@lru_cache
def get_settings() -> Settings:
    return Settings()
