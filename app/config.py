import json
from functools import lru_cache
from typing import List, Optional

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    env: str = Field("production", alias="ENV")
    database_url: str = Field(..., alias="DATABASE_URL")

    telegram_bot_token: str = Field("", alias="TELEGRAM_BOT_TOKEN")
    bot_username: str = Field("Slh_selha_bot", alias="BOT_USERNAME")

    base_url: str = Field("", alias="BASE_URL")
    frontend_api_base: str = Field("", alias="FRONTEND_API_BASE")
    frontend_bot_url: str = Field("https://t.me/Slh_selha_bot", alias="FRONTEND_BOT_URL")
    community_link: str = Field("https://t.me/+HIzvM8sEgh1kNWY0", alias="COMMUNITY_LINK")

    bsc_rpc_url: str = Field("", alias="BSC_RPC_URL")
    bscscan_api_key: str = Field("", alias="BSCSCAN_API_KEY")
    slh_token_address: str = Field("", alias="SLH_TOKEN_ADDRESS")

    secret_key: str = Field("change-me", alias="SECRET_KEY")
    payment_methods_raw: str = Field('["BNB","SLH","CREDIT_CARD","BANK_TRANSFER"]', alias="PAYMENT_METHODS")

    slh_ton_factor: float = Field(1000.0, alias="SLH_TON_FACTOR")

    admin_log_chat_id: Optional[str] = Field(None, alias="ADMIN_LOG_CHAT_ID")
    admin_dash_token: str = Field("", alias="ADMIN_DASH_TOKEN")

    cors_origins_raw: str = '["*"]'

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    @property
    def payment_methods(self) -> List[str]:
        try:
            return json.loads(self.payment_methods_raw)
        except Exception:
            return ["BNB", "SLH"]

    @property
    def cors_origins(self) -> List[str]:
        try:
            return json.loads(self.cors_origins_raw)
        except Exception:
            return ["*"]


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
