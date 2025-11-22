import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database import Base, engine
from .routers import wallet, trade
from .telegram_bot import router as telegram_router

logger = logging.getLogger("slh_wallet")


def setup_logging():
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )
    logger.info("Logging initialized with level %s", settings.log_level)


setup_logging()

# Create all tables if not exist
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SLH_Wallet_2.0",
    version="0.1.0",
    description="Unified SLH Wallet (BNB / SLH_BNB / SLH_TON) + Telegram Bot API",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files (CSS/JS)
app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "SLH_Wallet_2.0"}


@app.get("/api/meta")
async def api_meta():
    return settings.as_meta()


@app.get("/", response_class=HTMLResponse)
async def index_page():
    return FileResponse("frontend/index.html")


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
