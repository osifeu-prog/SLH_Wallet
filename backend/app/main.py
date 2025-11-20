
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import get_settings
from .db import Base, engine
from . import wallet_routes, trade_routes, auth_routes, admin_routes, telegram_bot
from .logger import logger

settings = get_settings()

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Unified BNB/SLH Wallet + Trading + Telegram Bot API",
    version="0.5.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/")
def index():
    return {
        "status": "ok",
        "name": settings.PROJECT_NAME,
        "env": settings.ENV,
        "base_url": settings.BASE_URL,
        "bot_url": settings.FRONTEND_BOT_URL,
        "community": settings.COMMUNITY_LINK,
    }

@app.get("/api/meta")
def api_meta():
    db_prefix = None
    if settings.DATABASE_URL:
        db_prefix = settings.DATABASE_URL.split(":", 1)[0]
    return {
        "service": "SLH_Wallet_2.0",
        "env": settings.ENV,
        "base_url": settings.BASE_URL,
        "bot_url": settings.FRONTEND_BOT_URL,
        "community": settings.COMMUNITY_LINK,
        "has_bot_token": bool(settings.TELEGRAM_BOT_TOKEN),
        "has_admin_log_chat": bool(settings.ADMIN_LOG_CHAT_ID),
        "db_url_prefix": db_prefix,
    }

# Routers
app.include_router(wallet_routes.router)
app.include_router(trade_routes.router)
app.include_router(auth_routes.router)
app.include_router(admin_routes.router)
app.include_router(telegram_bot.router)

logger.info(f"Started {settings.PROJECT_NAME} in ENV={settings.ENV}")
