import os
import json
from typing import List, Optional


class Settings:
    def __init__(self) -> None:
        self.env: str = os.getenv("ENV", "production")
        self.secret_key: str = os.getenv("SECRET_KEY", "change-me")

        self.database_url: str = os.getenv(
            "DATABASE_URL",
            "sqlite:///./slh_wallet.db",
        )

        self.telegram_bot_token: Optional[str] = os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_admin_chat_id: Optional[int] = None
        chat_id_raw = os.getenv("TELEGRAM_CHAT_ID")
        if chat_id_raw:
            try:
                self.telegram_admin_chat_id = int(chat_id_raw)
            except ValueError:
                self.telegram_admin_chat_id = None

        self.bot_username: Optional[str] = os.getenv("BOT_USERNAME")

        self.frontend_base_url: Optional[str] = os.getenv(
            "FRONTEND_API_BASE",
        )

        self.community_link: Optional[str] = os.getenv(
            "COMMUNITY_LINK",
            "https://t.me/+HIzvM8sEgh1kNWY0",
        )

        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")

        pm_raw = os.getenv(
            "PAYMENT_METHODS",
            '["BNB","SLH","CREDIT_CARD","BANK_TRANSFER"]',
        )
        try:
            self.payment_methods: List[str] = list(json.loads(pm_raw))
        except Exception:
            self.payment_methods = ["BNB", "SLH"]

    @property
    def base_url(self) -> str:
        return self.frontend_base_url or ""

    def as_meta(self) -> dict:
        return {
            "service": "SLH_Wallet_2.0",
            "env": self.env,
            "base_url": self.base_url,
            "bot_url": f"https://t.me/{self.bot_username}" if self.bot_username else None,
            "community": self.community_link,
        }


settings = Settings()
