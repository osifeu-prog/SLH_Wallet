
import json
import logging
import os
from functools import lru_cache
from typing import List, Optional

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings

logger = logging.getLogger("slh_wallet.config")


class Settings(BaseSettings):
    env: str = Field(default="development", alias="ENV")

    # Core service
    base_url: AnyHttpUrl | str = Field(
        default="https://thin-charlot-osifungar-d382d3c9.koyeb.app", alias="BASE_URL"
    )
    frontend_api_base: Optional[AnyHttpUrl | str] = Field(
        default=None, alias="FRONTEND_API_BASE"
    )

    # Database
    database_url: str = Field(..., alias="DATABASE_URL")

    # Telegram
    telegram_bot_token: str = Field(..., alias="TELEGRAM_BOT_TOKEN")
    bot_username: str | None = Field(default=None, alias="BOT_USERNAME")
    community_link: str | None = Field(default=None, alias="COMMUNITY_LINK")
    admin_log_chat_id: int | None = Field(default=None, alias="ADMIN_LOG_CHAT_ID")

    # Blockchain / SLH
    bsc_rpc_url: str = Field(
        default="https://bsc-dataseed.binance.org/", alias="BSC_RPC_URL"
    )
    slh_token_address: str = Field(..., alias="SLH_TOKEN_ADDRESS")
    bscscan_api_key: str | None = Field(default=None, alias="BSCSCAN_API_KEY")
    slh_ton_factor: float = Field(default=1000.0, alias="SLH_TON_FACTOR")

    payment_methods_raw: str | None = Field(default=None, alias="PAYMENT_METHODS")

    # Security
    secret_key: str = Field(..., alias="SECRET_KEY")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"

    @property
    def payment_methods(self) -> List[str]:
        raw = self.payment_methods_raw
        if not raw:
            return ["BNB", "SLH", "CREDIT_CARD", "BANK_TRANSFER"]
        if isinstance(raw, str):
            try:
                # allow both JSON list and simple comma-separated forms
                if raw.strip().startswith("["):
                    return json.loads(raw)
                return [x.strip() for x in raw.split(",") if x.strip()]
            except Exception as e:  # noqa: BLE001
                logger.warning("Failed to parse PAYMENT_METHODS=%r: %s", raw, e)
                return ["BNB", "SLH", "CREDIT_CARD", "BANK_TRANSFER"]
        return ["BNB", "SLH", "CREDIT_CARD", "BANK_TRANSFER"]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()  # type: ignore[call-arg]
    # Normalize URLs (strip trailing slash)
    if isinstance(settings.base_url, str):
        settings.base_url = settings.base_url.rstrip("/")
    if isinstance(settings.frontend_api_base, str):
        settings.frontend_api_base = settings.frontend_api_base.rstrip("/")
    return settings


settings = get_settings()
