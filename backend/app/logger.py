
import logging
from .config import get_settings

settings = get_settings()

logger = logging.getLogger("slh_wallet")
if not logger.handlers:
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(level)
    handler = logging.StreamHandler()
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s")
    handler.setFormatter(fmt)
    logger.addHandler(handler)
