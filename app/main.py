import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database import Base, engine
from .routers import wallet, trade
from .telegram_bot import router as telegram_router, get_application

logger = logging.getLogger("slh_wallet")


def setup_logging() -> None:
    """
    הגדרת לוגים בסיסית לכל השירות.
    """
    level_name = settings.log_level.upper()
    level = getattr(logging, level_name, logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )
    logger.info("Logging initialized with level %s", level_name)


app = FastAPI(
    title="SLH_Wallet_2.0",
    description="Unified SLH Wallet (BNB/SLH) + Bot API",
    version="0.1.0",
)


# CORS
origins = settings.get_cors_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if "*" not in origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Static files for frontend
app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.on_event("startup")
async def on_startup():
    # יצירת טבלאות אם לא קיימות
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ensured successfully")

    # לוגים
    setup_logging()

    # אתחול אפליקציית טלגרם (getMe וכו')
    try:
        app.state.telegram_app = await get_application()
        logger.info("Telegram Application initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize Telegram Application: %s", e)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "SLH_Wallet_2.0"}


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """
    דף ראשי – אפשר להפנות לדף הנחיתה.
    """
    return FileResponse("frontend/index.html")


@app.get("/api/meta")
async def api_meta():
    return settings.as_meta()


@app.get("/wallet", response_class=HTMLResponse)
async def wallet_page():
    return FileResponse("frontend/wallet.html")


@app.get("/landing", response_class=HTMLResponse)
async def landing_page():
    return FileResponse("frontend/index.html")


# Routers
app.include_router(wallet.router)
app.include_router(trade.router)
app.include_router(telegram_router)
