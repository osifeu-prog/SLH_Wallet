import logging
from pathlib import Path
from typing import List

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database import Base, engine
from .routers import wallet as wallet_router
from .routers import trade as trade_router
from .routers import admin as admin_router
from .telegram_bot import router as telegram_router

logger = logging.getLogger("slh_wallet")


def init_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )
    logger.info("Logging initialized with level %s", logging.getLevelName(logging.getLogger().level))


def create_app() -> FastAPI:
    init_logging()

    Base.metadata.create_all(bind=engine)

    app = FastAPI(
        title="SLH_Wallet_2.0",
        description="Unified SLH Wallet (BNB / SLH / TON) + Bot API + Community Exchange",
        version="0.2.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    static_dir = Path(__file__).resolve().parent.parent / "frontend"
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.get("/", response_class=HTMLResponse)
    async def index_page():
        return FileResponse(static_dir / "index.html")

    @app.get("/wallet", response_class=HTMLResponse)
    async def wallet_page():
        return FileResponse(static_dir / "wallet.html")

    @app.get("/admin", response_class=HTMLResponse)
    async def admin_page():
        return FileResponse(static_dir / "admin.html")

    @app.get("/api/meta")
    async def api_meta():
        return {
            "env": settings.env,
            "base_url": settings.base_url,
            "bot_username": settings.bot_username,
            "community_link": settings.community_link,
            "slh_ton_factor": settings.slh_ton_factor,
        }

    app.include_router(wallet_router.router)
    app.include_router(trade_router.router)
    app.include_router(admin_router.router)
    app.include_router(telegram_router)

    logger.info("=== Startup SLH_Wallet_2.0 FULL ===")
    return app


app = create_app()
