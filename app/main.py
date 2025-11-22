import logging
from pathlib import Path
from typing import List

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database import Base, engine, get_db
from .routers import wallet as wallet_router
from .routers import trade as trade_router
from .routers import admin as admin_router
from .telegram_bot import router as telegram_router

logger = logging.getLogger("slh_wallet")


def init_logging() -> None:
    """
    Basic logging setup for the service.

    לא תלוי ב-settings.log_level כדי לא לשבור סביבות ישנות.
    אם יש log_level ב-settings – נשתמש בו, אחרת INFO.
    """
    level_name = getattr(settings, "log_level", "INFO")
    level = getattr(logging, str(level_name).upper(), logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )
    logger.info("Logging initialized with level %s", logging.getLevelName(level))


def create_app() -> FastAPI:
    # לוגים + סכמת DB
    init_logging()
    Base.metadata.create_all(bind=engine)

    app = FastAPI(
        title="SLH_Wallet_2.0",
        description="Unified SLH Wallet (BNB/SLH) + Community P2P Exchange + Bot API",
        version="0.1.0",
    )

    # CORS
    origins: List[str] = getattr(settings, "cors_origins", ["*"])
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Static frontend
    static_dir = Path(__file__).resolve().parent.parent / "frontend"
    app.mount(
        "/static",
        StaticFiles(directory=static_dir),
        name="static",
    )

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.get("/", response_class=HTMLResponse)
    async def index_page():
        """
        דף הבית – בורסת הקהילה.
        """
        index_path = static_dir / "index.html"
        if index_path.is_file():
            return FileResponse(index_path)
        # fallback בסיסי אם אין קובץ
        return HTMLResponse("<h1>SLH • Community P2P Exchange</h1>", status_code=200)

    @app.get("/wallet", response_class=HTMLResponse)
    async def wallet_page(telegram_id: str | None = None):
        """
        דף הארנק – כרגע בעיקר הסבר. הפעולות עצמן דרך הבוט.
        """
        wallet_path = static_dir / "wallet.html"
        if wallet_path.is_file():
            return FileResponse(wallet_path)
        return HTMLResponse(
            "<h1>SLH Wallet</h1><p>הארנק מנוהל דרך בוט הטלגרם.</p>",
            status_code=200,
        )

    @app.get("/admin", response_class=HTMLResponse)
    async def admin_page():
        """
        דף אדמין (כרגע placeholder / סטטי).
        """
        admin_path = static_dir / "admin.html"
        if admin_path.is_file():
            return FileResponse(admin_path)
        return HTMLResponse("<h1>SLH Admin</h1>", status_code=200)

    @app.get("/academy/money", response_class=HTMLResponse)
    async def academy_money():
        """
        דף לימודי: מבוא לכסף קהילתי ו-SLH.
        """
        html_path = static_dir / "academy" / "money.html"
        if html_path.is_file():
            return FileResponse(html_path)
        return HTMLResponse(
            "<h1>SLH Academy</h1><p>Lesson page not found.</p>",
            status_code=404,
        )

    @app.get("/api/meta")
    async def api_meta():
        """
        מידע כללי – לשימוש פרונט / בוט / אופס.
        """
        return {
            "env": settings.env,
            "base_url": settings.base_url,
            "bot_username": settings.bot_username,
            "community_link": getattr(settings, "community_link", None),
            "slh_ton_factor": getattr(settings, "slh_ton_factor", None),
        }

    # Routers – API אמיתי
    app.include_router(wallet_router.router)
    app.include_router(trade_router.router)
    app.include_router(admin_router.router)
    app.include_router(telegram_router)

    logger.info("=== Startup SLH_Wallet_2.0 FULL ===")
    return app


app = create_app()
