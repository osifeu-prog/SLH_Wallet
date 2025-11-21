import logging
from typing import Dict, Optional

import aiohttp
import os

from .config import settings

logger = logging.getLogger("slh_wallet.blockchain")


class BlockchainService:
    """
    שירות קטן לשאיבת יתרות BNB ו-SLH באמצעות BscScan.
    אם אין API KEY – מחזיר 0 ומדפיס אזהרה ללוג.
    """

    def __init__(self) -> None:
        self.bscscan_api_key = settings.bscscan_api_key
        self.bsc_rpc_url = os.getenv("BSC_RPC_URL", "https://bsc-dataseed.binance.org/")
        self.slh_token_address = settings.slh_token_address

    async def _get_json(self, url: str, params: Dict) -> Optional[Dict]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as resp:
                    if resp.status != 200:
                        logger.warning("BscScan non-200 status: %s", resp.status)
                        return None
                    return await resp.json()
        except Exception as e:
            logger.error("Error calling BscScan: %s", e)
            return None

    async def get_bnb_balance(self, address: str) -> Optional[float]:
        """מקבל את יתרת BNB מכתובת"""
        if not address:
            return 0.0

        if not self.bscscan_api_key:
            logger.warning("BSCSCAN_API_KEY not set – returning BNB balance = 0")
            return 0.0

        url = "https://api.bscscan.com/api"
        params = {
            "module": "account",
            "action": "balance",
            "address": address,
            "tag": "latest",
            "apikey": self.bscscan_api_key,
        }

        data = await self._get_json(url, params)
        if not data or data.get("status") != "1":
            logger.warning("BscScan BNB balance error response: %s", data)
            return 0.0

        try:
            raw = int(data.get("result", "0"))
            return raw / 10**18
        except Exception as e:
            logger.error("Error parsing BNB balance: %s", e)
            return 0.0

    async def get_slh_balance(self, address: str) -> Optional[float]:
        """מקבל את יתרת טוקן SLH מהחוזה"""
        if not address:
            return 0.0

        if not self.bscscan_api_key or not self.slh_token_address:
            logger.warning("BSCSCAN_API_KEY or SLH_TOKEN_ADDRESS not set – SLH balance = 0")
            return 0.0

        url = "https://api.bscscan.com/api"
        params = {
            "module": "account",
            "action": "tokenbalance",
            "contractaddress": self.slh_token_address,
            "address": address,
            "tag": "latest",
            "apikey": self.bscscan_api_key,
        }

        data = await self._get_json(url, params)
        if not data or data.get("status") != "1":
            logger.warning("BscScan token balance error response: %s", data)
            return 0.0

        try:
            # נניח גם כאן 18 ספרות אחרי הנקודה
            raw = int(data.get("result", "0"))
            return raw / 10**18
        except Exception as e:
            logger.error("Error parsing SLH balance: %s", e)
            return 0.0

    async def get_balances(self, bnb_address: str, slh_address: str) -> Dict[str, float]:
        """מחזיר את כל היתרות עבור ארנק אחד"""
        bnb_balance = await self.get_bnb_balance(bnb_address)
        slh_balance = await self.get_slh_balance(slh_address or bnb_address)

        return {
            "bnb": float(bnb_balance or 0.0),
            "slh": float(slh_balance or 0.0),
        }


blockchain_service = BlockchainService()
