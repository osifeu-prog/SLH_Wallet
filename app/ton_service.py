import logging

logger = logging.getLogger("slh_wallet.ton")


class TonService:
    def __init__(self) -> None:
        # בעתיד נחבר לכאן את TON API שלך (SLHMAINNET)
        pass

    async def get_slh_ton_balance(self, address: str) -> float:
        # כרגע החזר לוגי בלבד – עד שנחבר API אמיתי
        if not address:
            return 0.0
        return 0.0


ton_service = TonService()
