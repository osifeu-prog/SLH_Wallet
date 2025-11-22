import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database import Base, engine
from .db_schema import ensure_schema

# Ensure DB schema (idempotent, safe on each startup)
ensure_schema()
from .routers import wallet, trade
from .telegram_bot import router as telegram_router, get_application

logger = logging.getLogger("slh_wallet")


def setup_logging():
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def init_db():
    """✅ אתחול מסד נתונים - מוודא שהטבלות מעודכנות"""
    try:
        # מחיקת הטבלות הקיימות ויצירתן מחדש עם הסכימה המעודכנת
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables recreated successfully")
    except Exception as e:
        logger.error("Error initializing database: %s", e)
        raise


app = FastAPI(
    title="SLH_Wallet_2.0",
    version="0.1.0",
    description="Unified SLH Wallet (BNB/SLH) + Bot API",
)


@app.on_event("startup")
async def on_startup():
    setup_logging()
    init_db()
    logger.info("=== Startup SLH_Wallet_2.0 ===")

    if settings.telegram_bot_token:
        try:
            await get_application()
            logger.info("Telegram Application initialized successfully")
        except Exception as exc:
            logger.error("Failed to initialize Telegram Bot: %s", exc)
    else:
        logger.warning("TELEGRAM_BOT_TOKEN is not set - bot is disabled")


# ✅ CORS מאובטח
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    allow_credentials=True,
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info("[WEB] %s %s", request.method, request.url.path)
    response = await call_next(request)
    logger.info("[WEB] %s %s -> %s", request.method, request.url.path, response.status_code)
    return response


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/")
async def index():
    meta = settings.as_meta()
    return {
        "status": "ok",
        "name": meta["service"],
        "env": meta["env"],
        "base_url": meta["base_url"],
        "bot_url": meta["bot_url"],
        "community": meta["community"],
    }


@app.get("/api/meta")
async def api_meta():
    meta = settings.as_meta()
    return {
        **meta,
        "has_bot_token": bool(settings.telegram_bot_token),
        "has_admin_log_chat": bool(settings.telegram_admin_chat_id),
        "db_url_prefix": settings.database_url.split(":", 1)[0],
        "security": {
            "cors_restricted": len(settings.allowed_origins) > 0 and "*" not in settings.allowed_origins,
            "secret_key_configured": settings.secret_key != "change-me",
        }
    }


app.mount(
    "/static",
    StaticFiles(directory="frontend"),
    name="static",
)


@app.get("/wallet", response_class=HTMLResponse)
async def wallet_page():
    return FileResponse("frontend/wallet.html")


@app.get("/landing", response_class=HTMLResponse)
async def landing_page():
    return FileResponse("frontend/index.html")


app.include_router(wallet.router)
app.include_router(trade.router)
app.include_router(telegram_router)