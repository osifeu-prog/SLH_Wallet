import logging
from typing import Dict, Optional
import aiohttp
import os
from .config import settings

logger = logging.getLogger("slh_wallet.blockchain")

class BlockchainService:
    def __init__(self):
        self.bscscan_api_key = settings.bscscan_api_key
        self.bsc_rpc_url = os.getenv("BSC_RPC_URL", "https://bsc-dataseed.binance.org/")
        self.slh_token_address = settings.slh_token_address

    async def get_bnb_balance(self, address: str) -> Optional[float]:
        """מקבל את יתרת BNB מכתובת"""
        try:
            if not address or address == "0x" or len(address) < 10:
                return 0.0
                
            async with aiohttp.ClientSession() as session:
                # באמצעות BscScan API
                if self.bscscan_api_key:
                    url = f"https://api.bscscan.com/api?module=account&action=balance&address={address}&tag=latest&apikey={self.bscscan_api_key}"
                    async with session.get(url) as response:
                        data = await response.json()
                        if data.get('status') == '1':
                            balance_wei = int(data['result'])
                            return balance_wei / 10**18

                # גיבוי עם RPC
                payload = {
                    "jsonrpc": "2.0",
                    "method": "eth_getBalance",
                    "params": [address, "latest"],
                    "id": 1
                }
                async with session.post(self.bsc_rpc_url, json=payload) as response:
                    data = await response.json()
                    if 'result' in data:
                        balance_wei = int(data['result'], 16)
                        return balance_wei / 10**18
                        
        except Exception as e:
            logger.error("Error fetching BNB balance for %s: %s", address, e)
            
        return 0.0

    async def get_slh_balance(self, address: str) -> Optional[float]:
        """מקבל את יתרת SLH Token"""
        try:
            if not address or address == "0x" or not self.slh_token_address:
                return 0.0

            # TODO: Implement actual SLH token balance check using web3
            # For now return mock data
            return 1500.0  # Mock data
            
        except Exception as e:
            logger.error("Error fetching SLH balance for %s: %s", address, e)
            
        return 0.0

    async def get_balances(self, bnb_address: str, slh_address: str) -> Dict[str, float]:
        """מחזיר את כל היתרות"""
        bnb_balance = await self.get_bnb_balance(bnb_address)
        slh_balance = await self.get_slh_balance(slh_address or bnb_address)
        
        return {
            "bnb": bnb_balance,
            "slh": slh_balance,
        }


blockchain_service = BlockchainService()
