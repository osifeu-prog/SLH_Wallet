import logging
from .config import settings


logger = logging.getLogger("slh_wallet")

level = getattr(logging, settings.log_level.upper(), logging.INFO)
logger.setLevel(level)

if not logger.handlers:
    ch = logging.StreamHandler()
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s")
    ch.setFormatter(fmt)
    logger.addHandler(ch)


async def log_event(kind: str, message: str) -> None:
    """
    Simple async-compatible logging helper used across the project.
    """
    logger.info("[%s] %s", kind.upper(), message)
