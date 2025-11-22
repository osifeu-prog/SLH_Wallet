import os
import json
from typing import List, Optional


class Settings:
    """
    Central configuration object for the SLH Wallet service.
    Reads from environment variables provided by Koyeb / .env.
    """

    def __init__(self) -> None:
        # Environment
        self.env: str = os.getenv("ENV", "production")

        # Core secrets
        self.secret_key: str = os.getenv("SECRET_KEY", "change-me")
        if self.env == "production" and self.secret_key == "change-me":
            raise ValueError("SECRET_KEY must be set in production environment!")

        # Database
        self.database_url: str = os.getenv("DATABASE_URL", "")

        # Logging
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")

        # Telegram
        self.telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.bot_username: Optional[str] = os.getenv("BOT_USERNAME") or None
        self.admin_log_chat_id: Optional[str] = os.getenv("ADMIN_LOG_CHAT_ID") or None

        # URLs / Frontend
        self.base_url: str = os.getenv("BASE_URL", "").rstrip("/")
        self.frontend_api_base: str = os.getenv("FRONTEND_API_BASE", self.base_url).rstrip("/")
        self.frontend_bot_url: Optional[str] = os.getenv("FRONTEND_BOT_URL") or None
        self.community_link: Optional[str] = os.getenv("COMMUNITY_LINK") or None

        # Blockchain – BNB / SLH
        self.bscscan_api_key: Optional[str] = os.getenv("BSCSCAN_API_KEY") or None
        self.bsc_rpc_url: str = os.getenv("BSC_RPC_URL", "https://bsc-dataseed.binance.org/")
        self.slh_token_address: Optional[str] = os.getenv("SLH_TOKEN_ADDRESS") or None

        # Blockchain – TON / SLH_TON
        self.ton_api_key: Optional[str] = os.getenv("TON_API_KEY") or None
        # Logical factor between SLH_TON and SLH_BNB (1 SLH_TON = factor * SLH_BNB)
        try:
            self.slh_ton_factor: float = float(os.getenv("SLH_TON_FACTOR", "1000"))
        except ValueError:
            self.slh_ton_factor = 1000.0

        # Payment methods (for future use in docs / UI)
        payment_methods_raw = os.getenv("PAYMENT_METHODS", "[]")
        try:
            self.payment_methods: List[str] = json.loads(payment_methods_raw)
        except Exception:
            self.payment_methods = []

        # Internal API base (for the bot to call HTTP if needed)
        self.internal_api_base: str = os.getenv("INTERNAL_API_BASE", "http://127.0.0.1:8000").rstrip("/")

    @property
    def cors_origins(self) -> List[str]:
        """
        Derive a safe list of CORS origins based on base URL / frontend URLs.
        """
        origins: List[str] = []
        for url in (self.base_url, self.frontend_api_base, self.frontend_bot_url, self.community_link):
            if url and url.startswith("http"):
                origins.append(url.rstrip("/"))
        # Always allow localhost for local testing
        origins.append("http://localhost")
        origins.append("http://127.0.0.1")
        return sorted(set(origins))

    def as_meta(self) -> dict:
        """
        Small meta payload for /api/meta endpoint.
        """
        return {
            "service": "SLH_Wallet_2.0",
            "env": self.env,
            "base_url": self.base_url,
            "frontend_api_base": self.frontend_api_base,
            "bot_username": self.bot_username,
            "bot_url": f"https://t.me/{self.bot_username}" if self.bot_username else None,
            "community": self.community_link,
            "payment_methods": self.payment_methods,
            "slh_token_address": self.slh_token_address,
            "slh_ton_factor": self.slh_ton_factor,
        }


settings = Settings()
