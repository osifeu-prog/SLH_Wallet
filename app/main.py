
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config import settings
from .database import Base, engine
from .db_schema import ensure_schema
from .routers import wallet as wallet_router
from .routers import trade as trade_router
from .telegram_bot import router as telegram_router

logger = logging.getLogger("slh_wallet.main")
logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))

# Ensure schema is in place
ensure_schema(engine)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SLH Wallet 2.0",
    description="Unified SLH Wallet (BNB/TON/SLH Internal) + Bot API",
    version="0.2.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static + templates
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
templates = Jinja2Templates(directory="frontend")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "bot_url": settings.bot_username and f"https://t.me/{settings.bot_username}" or "",
            "community_link": settings.community_link,
        },
    )


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/api/meta")
async def api_meta():
    return {
        "service": "slh_wallet",
        "env": settings.env,
        "base_url": str(settings.base_url),
    }


# Routers
app.include_router(wallet_router.router)
app.include_router(trade_router.router)
app.include_router(telegram_router)
