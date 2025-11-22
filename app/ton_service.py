import logging
from typing import Optional
import aiohttp
from .config import settings

logger = logging.getLogger("slh_wallet.ton")


class TonService:
    """
    Minimal TON API wrapper for SLH_TON balances.
    For now this is a placeholder that can be wired to your actual TON API.
    """

    def __init__(self) -> None:
        self.api_key = settings.ton_api_key
        self.network = "mainnet"

    async def get_ton_balance(self, address: str) -> float:
        """
        Native TON balance (optional, for future use).
        """
        if not address or not self.api_key:
            return 0.0

        # TODO: Implement actual TON API call here.
        # For now, we return 0.0 so the system is ready for when tokens exist.
        return 0.0

    async def get_slh_ton_balance(self, address: str) -> float:
        """
        SLH_TON token balance for a given TON address.
        """
        if not address or not self.api_key:
            return 0.0

        # TODO: Implement your TON token balance fetch.
        # For now, returns 0.0 until SLH_TON is live.
        return 0.0


ton_service = TonService()
