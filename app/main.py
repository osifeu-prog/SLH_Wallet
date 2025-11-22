import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database import Base, engine
from .db_schema import ensure_schema
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
async def wallet_page(request: Request):
    """Legacy entry point from the bot.

    אם מגיעים עם פרמטר telegramid – מפנים לאזור האישי החדש /u/{telegram_id}.
    אחרת מציגים דף נחיתה כללי.
    """
    telegram_id = request.query_params.get("telegramid") or request.query_params.get("telegram_id")
    if telegram_id:
        # הפניה רכה לאזור האישי
        return RedirectResponse(url=f"/u/{telegram_id}", status_code=307)
    # כניסה ישירה – מציגים את דף הלימוד / ארנק כללי
    return FileResponse("frontend/wallet.html")


@app.get("/landing", response_class=HTMLResponse)
async def landing_page():
    return FileResponse("frontend/index.html")



from .database import SessionLocal
from . import models, blockchain_service


@app.get("/u/{telegram_id}", response_class=HTMLResponse)
async def user_hub(telegram_id: str):
    """אזור אישי של משתמש – מוצג לקריאה בלבד.

    ✳ זהות מבוססת Telegram ID + כתובות ארנק.
    ✳ אין הקלדה של סיסמאות או פרטים רגישים באתר – הכול נעשה דרך הבוט.
    """
    db = SessionLocal()
    try:
        wallet = db.get(models.Wallet, telegram_id)
    finally:
        db.close()

    if not wallet:
        html = f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
  <meta charset="UTF-8" />
  <title>SLH Wallet – לא נמצא ארנק</title>
  <link rel="stylesheet" href="/static/css/style.css" />
</head>
<body class="slh-body">
  <div class="slh-container">
    <h1>SLH Wallet</h1>
    <p>לא נמצא ארנק עבור Telegram ID: <strong>{telegram_id}</strong>.</p>
    <p>כדי לפתוח ארנק, חזור לבוט הרשמי והרץ את הפקודה <code>/wallet</code>.</p>
    <p><a href="{settings.frontend_bot_url}" target="_blank">פתיחת הבוט בטלגרם</a></p>
  </div>
</body>
</html>"""
        return HTMLResponse(content=html)

    # מנסים להביא יתרות BNB/SLH מהרשת
    balances = None
    try:
        if wallet.bnb_address:
            balances = await blockchain_service.get_balances(
                wallet.bnb_address,
                wallet.slh_address or wallet.bnb_address,
            )
    except Exception as e:  # noqa: BLE001
        logger.warning("Failed to fetch blockchain balances for %s: %s", telegram_id, e)
        balances = None

    bnb_balance = balances["bnb"] if balances else None
    slh_balance = balances["slh"] if balances else None

    # URL לכרטיס האישי / הזמנת חבר
    invite_url = f"{settings.frontend_bot_url}?start=ref_{telegram_id}"

    html = f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
  <meta charset="UTF-8" />
  <title>SLH Wallet – האזור האישי</title>
  <link rel="stylesheet" href="/static/css/style.css" />
  <script src="https://cdnjs.cloudflare.com/ajax/libs/qrious/4.0.2/qrious.min.js"></script>
</head>
<body class="slh-body">
  <div class="slh-container slh-card">
    <h1>הכרטיס הדיגיטלי של הקהילה – SLH</h1>
    <p>זהו האזור האישי שלך במערכת. כל הניהול נעשה דרך הבוט – האתר מציג עבורך את המצב.</p>

    <section class="slh-section">
      <h2>פרטי משתמש</h2>
      <ul>
        <li><strong>Telegram ID:</strong> {wallet.telegram_id}</li>
        <li><strong>שם משתמש:</strong> @{wallet.username or ""}</li>
        <li><strong>שם:</strong> {wallet.first_name or ""} {wallet.last_name or ""}</li>
      </ul>
    </section>

    <section class="slh-section">
      <h2>כתובות ארנק</h2>
      <ul>
        <li><strong>BNB / BSC:</strong> {wallet.bnb_address or "עדיין לא הוגדר"}</li>
        <li><strong>SLH על BNB:</strong> {wallet.slh_address or wallet.bnb_address or "עדיין לא הוגדר"}</li>
        <li><strong>SLH על TON:</strong> {wallet.slh_ton_address or "עדיין לא הוגדר"}</li>
      </ul>
      <p>כדי לעדכן כתובות ארנק, חזור לבוט והשתמש בפקודות /set_bnb ו-/set_ton.</p>
    </section>

    <section class="slh-section">
      <h2>יתרות (תצוגה בלבד)</h2>
      <ul>
        <li><strong>BNB ברשת BSC:</strong> {bnb_balance if bnb_balance is not None else "נדרש סנכרון"}</li>
        <li><strong>SLH על BNB:</strong> {slh_balance if slh_balance is not None else "נדרש סנכרון"}</li>
        <li><strong>SLH פנימי (לגרעין הכלכלי):</strong> יוצג בהמשך</li>
      </ul>
    </section>

    <section class="slh-section slh-card qr-card">
      <h2>קישור ו-QR לשיתוף</h2>
      <p>זהו קישור ההפניה האישי שלך. חברים שייכנסו דרכו יזוהו כשייכים אליך.</p>
      <p><a href="{invite_url}" target="_blank">{invite_url}</a></p>
      <canvas id="qr"></canvas>
      <script>
        (function() {{
          var qr = new QRious({{
            element: document.getElementById('qr'),
            value: '{invite_url}',
            size: 180
          }});
        }})();
      </script>
    </section>

    <section class="slh-section">
      <h2>ניהול מתקדם</h2>
      <ul>
        <li>לניהול פרטי בנק: השתמש בפקודה <code>/bank</code> בבוט.</li>
        <li>לצפייה ביתרות פנימיות והיסטוריית עסקאות: <code>/balances</code> (בקרוב גרסת אתר מלאה).</li>
        <li>להצטרפות לקבוצת הבורסה והקהילה: <a href="{settings.community_link}" target="_blank">פתיחת הקבוצה</a></li>
      </ul>
    </section>

    <footer class="slh-footer">
      <p>SLH – Human Capital Protocol · אין סיסמאות, אין טפסים מיותרים · זהות = ארנק + טלגרם.</p>
    </footer>
  </div>
</body>
</html>"""
    return HTMLResponse(content=html)

app.include_router(wallet.router)
app.include_router(trade.router)
app.include_router(telegram_router)
