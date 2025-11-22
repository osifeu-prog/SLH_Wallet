
import logging
from .config import get_settings

settings = get_settings()

logger = logging.getLogger("slh_wallet")
level = logging.getLevelName(settings.LOG_LEVEL.upper()) if hasattr(logging, settings.LOG_LEVEL.upper()) else logging.INFO
logger.setLevel(level)

if not logger.handlers:
    ch = logging.StreamHandler()
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s")
    ch.setFormatter(fmt)
    logger.addHandler(ch)


async def log_event(kind: str, message: str):
    logger.info("[%s] %s", kind.upper(), message)
