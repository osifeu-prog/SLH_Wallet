import os
import json
from typing import List, Optional


class Settings:
    """
    מרכזת את כל ההגדרות מה-ENV במקום אחד.
    בנויה כך שתתאים גם לקוד הישן וגם לקוד החדש.
    """

    def __init__(self) -> None:
        # בסיסי
        self.env: str = os.getenv("ENV", "development")

        # SECRET_KEY מאובטח
        self.secret_key: str = os.getenv("SECRET_KEY", "change-me")
        if self.env == "production" and self.secret_key == "change-me":
            raise ValueError("SECRET_KEY must be set in production environment!")

        # Database
        self.database_url: str = os.getenv(
            "DATABASE_URL",
            "sqlite:///./slh_wallet.db",
        )

        # Base / Frontend
        self.base_url: str = os.getenv("BASE_URL", "").rstrip("/")
        self.frontend_api_base: str = os.getenv(
            "FRONTEND_API_BASE",
            self.base_url,
        ).rstrip("/")
        self.frontend_bot_url: str = os.getenv("FRONTEND_BOT_URL", "")
        self.community_link: str = os.getenv("COMMUNITY_LINK", "")

        # Telegram bot
        self.telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.bot_username: str = os.getenv("BOT_USERNAME", "")
        self.admin_log_chat_id: Optional[int] = None
        raw_admin_chat = os.getenv("ADMIN_LOG_CHAT_ID")
        if raw_admin_chat:
            try:
                self.admin_log_chat_id = int(raw_admin_chat)
            except ValueError:
                self.admin_log_chat_id = None

        # Logging
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")

        # Blockchain / SLH
        self.bscscan_api_key: str = os.getenv("BSCSCAN_API_KEY", "")
        self.slh_token_address: str = os.getenv("SLH_TOKEN_ADDRESS", "").lower()

        # אמצעי תשלום
        raw_payment_methods = os.getenv("PAYMENT_METHODS", "[]")
        self.payment_methods: List[str] = []
        try:
            parsed = json.loads(raw_payment_methods)
            if isinstance(parsed, list):
                self.payment_methods = [str(x) for x in parsed]
        except json.JSONDecodeError:
            # פורמט רגיל עם פסיקים
            self.payment_methods = [
                p.strip() for p in raw_payment_methods.split(",") if p.strip()
            ]

        # CORS
        self._allowed_origins_raw: str = os.getenv("ALLOWED_ORIGINS", "")

    # התאמה ל-logging_utils הישן – מצפה ל-LOG_LEVEL באותיות גדולות
    @property
    def LOG_LEVEL(self) -> str:
        return self.log_level

    def get_cors_origins(self) -> List[str]:
        """
        מחזיר רשימת origins חוקיים ל-CORS.
        תמיד מוסיף את base_url ו-frontend_api_base אם קיימים.
        """
        origins: List[str] = []

        raw = self._allowed_origins_raw.strip()
        if not raw or raw == "*":
            origins = ["*"]
        else:
            # אפשר גם JSON וגם רשימת פסיקים
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    origins = [str(x).rstrip("/") for x in parsed]
            except json.JSONDecodeError:
                origins = [o.strip().rstrip("/") for o in raw.split(",") if o.strip()]

        # לוודא שה-BASE_URL וה-FRONTEND_API_BASE בפנים
        for extra in (self.base_url, self.frontend_api_base):
            if extra and extra not in origins and "*" not in origins:
                origins.append(extra)

        # לשימוש פנימי אם צריך
        return origins

    def as_meta(self) -> dict:
        """Meta info ל-/api/meta"""
        return {
            "service": "SLH_Wallet_2.0",
            "env": self.env,
            "base_url": self.base_url,
            "frontend_api_base": self.frontend_api_base,
            "bot_username": self.bot_username,
            "bot_url": f"https://t.me/{self.bot_username}" if self.bot_username else None,
            "community": self.community_link,
            "payment_methods": self.payment_methods,
        }


_settings = Settings()


def get_settings() -> Settings:
    return _settings


settings = _settings
