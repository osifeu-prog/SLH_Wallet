import logging
from typing import Dict

from web3 import Web3
from .config import settings

logger = logging.getLogger("slh_wallet.blockchain")


class BlockchainService:
    def __init__(self) -> None:
        self.rpc_url = settings.bsc_rpc_url
        self.slh_token_address = settings.slh_token_address
        self.web3 = Web3(Web3.HTTPProvider(self.rpc_url)) if self.rpc_url else None

        # מינימלי ל-ERC20
        self.erc20_abi = [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function",
            }
        ]

    async def get_bnb_balance(self, address: str) -> float:
        if not self.web3 or not address:
            return 0.0
        try:
            balance_wei = self.web3.eth.get_balance(Web3.to_checksum_address(address))
            return self.web3.from_wei(balance_wei, "ether")
        except Exception as e:
            logger.error("Error fetching BNB balance for %s: %s", address, e)
            return 0.0

    async def get_slh_balance(self, address: str) -> float:
        if not self.web3 or not address or not self.slh_token_address:
            return 0.0
        try:
            contract = self.web3.eth.contract(
                address=Web3.to_checksum_address(self.slh_token_address),
                abi=self.erc20_abi,
            )
            balance = contract.functions.balanceOf(Web3.to_checksum_address(address)).call()
            # נניח 18 ספרות אחרי הנקודה
            return balance / (10 ** 18)
        except Exception as e:
            logger.error("Error fetching SLH balance for %s: %s", address, e)
            return 0.0

    async def get_balances(self, bnb_address: str, slh_address: str) -> Dict[str, float]:
        bnb = await self.get_bnb_balance(bnb_address) if bnb_address else 0.0
        slh = await self.get_slh_balance(slh_address or bnb_address) if (slh_address or bnb_address) else 0.0
        return {"bnb": float(bnb), "slh": float(slh)}


blockchain_service = BlockchainService()
