import logging
from typing import Dict, Optional
import aiohttp
from .config import settings

logger = logging.getLogger("slh_wallet.blockchain")


class BlockchainService:
    """
    Thin wrapper around BscScan (or compatible) API
    for reading BNB and SLH token balances.
    """

    def __init__(self) -> None:
        self.bscscan_api_key = settings.bscscan_api_key
        self.bsc_rpc_url = settings.bsc_rpc_url
        self.slh_token_address = (settings.slh_token_address or "").lower()

    async def _call_bscscan(self, params: Dict[str, str]) -> Optional[Dict]:
        if not self.bscscan_api_key:
            logger.warning("BSCSCAN_API_KEY not configured")
            return None

        url = "https://api.bscscan.com/api"
        params = dict(params)
        params["apikey"] = self.bscscan_api_key

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as resp:
                    if resp.status != 200:
                        logger.error("BscScan HTTP error %s", resp.status)
                        return None
                    data = await resp.json()
                    if data.get("status") != "1":
                        logger.warning("BscScan non-success response: %s", data)
                        return None
                    return data
        except Exception as e:
            logger.exception("Error calling BscScan: %s", e)
            return None

    async def get_bnb_balance(self, address: str) -> Optional[float]:
        if not address:
            return 0.0

        data = await self._call_bscscan(
            {
                "module": "account",
                "action": "balance",
                "address": address,
                "tag": "latest",
            }
        )
        if not data:
            return 0.0

        try:
            wei = int(data.get("result", "0"))
            return wei / 10**18
        except Exception:
            logger.exception("Failed parsing BNB balance")
            return 0.0

    async def get_slh_balance(self, address: str) -> Optional[float]:
        """
        Reads SLH (ERC-20) balance for a given address.
        If no dedicated SLH address is configured, falls back to BNB address.
        """
        if not address or not self.slh_token_address:
            return 0.0

        data = await self._call_bscscan(
            {
                "module": "account",
                "action": "tokenbalance",
                "contractaddress": self.slh_token_address,
                "address": address,
                "tag": "latest",
            }
        )
        if not data:
            return 0.0

        try:
            raw = int(data.get("result", "0"))
            # Assuming SLH has 18 decimals – adjust if different
            return raw / 10**18
        except Exception:
            logger.exception("Failed parsing SLH balance")
            return 0.0

    async def get_balances(self, bnb_address: Optional[str], slh_address: Optional[str]) -> Dict[str, float]:
        """
        Convenience helper – returns both BNB and SLH balances.
        """
        bnb_addr = bnb_address or ""
        slh_addr = slh_address or bnb_addr

        bnb_balance = await self.get_bnb_balance(bnb_addr)
        slh_balance = await self.get_slh_balance(slh_addr)

        return {
            "bnb": bnb_balance,
            "slh": slh_balance,
        }


blockchain_service = BlockchainService()
