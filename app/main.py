
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pathlib import Path

from .config import get_settings
from .database import Base, engine
from .logging_utils import logger
from . import router_wallet, router_trade, telegram_bot

settings = get_settings()

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SLH_Wallet_2.0",
    version="0.1.0",
    description="Unified SLH Wallet (BNB/SLH) + Bot API",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # אפשר להקשיח בהמשך
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static / frontend
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    resp = await call_next(request)
    path = request.url.path
    logger.info("[WEB] %s %s -> %s", request.method, path, resp.status_code)
    return resp


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/")
async def index():
    meta = {
        "status": "ok",
        "name": "SLH_Wallet_2.0",
        "env": settings.ENV,
        "base_url": settings.BASE_URL,
        "bot_url": settings.FRONTEND_BOT_URL,
        "community": settings.COMMUNITY_LINK,
    }
    # אם יש index.html בפרונטנד – נחזיר אותו
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return JSONResponse(meta)


@app.get("/api/meta")
async def api_meta():
    return {
        "service": "SLH_Wallet_2.0",
        "env": settings.ENV,
        "base_url": settings.BASE_URL,
        "bot_url": settings.FRONTEND_BOT_URL,
        "community": settings.COMMUNITY_LINK,
        "has_bot_token": bool(settings.TELEGRAM_BOT_TOKEN),
        "has_admin_log_chat": bool(settings.ADMIN_LOG_CHAT_ID),
        "db_url_prefix": (settings.DATABASE_URL or "sqlite").split(":", 1)[0],
    }


# Routers
app.include_router(router_wallet.router)
app.include_router(router_trade.router)
app.include_router(telegram_bot.router)
