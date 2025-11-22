import os
import json
from typing import List, Optional


class Settings:
    def __init__(self) -> None:
        self.env: str = os.getenv("ENV", "production")
        
        # ✅ SECRET_KEY מאובטח
        self.secret_key: str = os.getenv("SECRET_KEY", "change-me")
        if self.env == "production" and self.secret_key == "change-me":
            raise ValueError("SECRET_KEY must be set in production environment!")

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

        # ✅ API keys for blockchain
        self.bscscan_api_key: str = os.getenv("BSCSCAN_API_KEY", "")
        self.slh_token_address: str = os.getenv("SLH_TOKEN_ADDRESS", "0xACb0A09414CEA1C879c67bB7A877E4e19480f022")

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

    @property
    def allowed_origins(self) -> List[str]:
        """✅ CORS מאובטח - רק דומיינים מורשים"""
        if self.env == "development":
            return [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:8000",
            ]
        else:
            origins = []
            if self.base_url:
                origins.append(self.base_url.rstrip('/'))
            return origins

    def as_meta(self) -> dict:
        return {
            "service": "SLH_Wallet_2.0",
            "env": self.env,
            "base_url": self.base_url,
            "bot_url": f"https://t.me/{self.bot_username}" if self.bot_username else None,
            "community": self.community_link,
        }


settings = Settings()
