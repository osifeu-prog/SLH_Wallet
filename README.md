
# SLH_Wallet_2.0

Unified SLH Wallet (BNB/SLH) + Telegram Bot + Web Dashboard.

## Structure

- `backend/` – FastAPI app (exposed as `app.main:app`)
- `frontend/` – Static landing + wallet/trade UI
- `start.sh` – Entry script for Koyeb/Render/Docker
- `requirements.txt` – Python dependencies

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

export ENV=development
export BASE_URL=http://127.0.0.1:8000
uvicorn app.main:app --reload --app-dir backend
```

Then open: http://127.0.0.1:8000/

## Deploy on Koyeb

- Connect this repo
- Buildpack
- Run command: `bash start.sh`
- Expose port 8000

### Required env vars (Koyeb Secrets)

- `ENV=production`
- `BASE_URL=https://YOUR-KOYEB-APP.koyeb.app`
- `SECRET_KEY=some-long-random`
- `DATABASE_URL=postgresql://...` (Neon/Supabase/etc). If omitted -> sqlite file.
- `BSC_RPC_URL=https://bsc-dataseed.binance.org/`
- `TELEGRAM_BOT_TOKEN=...`
- `ADMIN_LOG_CHAT_ID=-100...` (Telegram group/channel id for logs)
- `FRONTEND_BOT_URL=https://t.me/YourBot`
- `COMMUNITY_LINK=https://t.me/YourCommunity`

## API

- `GET /health`
- `GET /` – landing or JSON meta
- `GET /api/meta`
- `POST /api/wallet/register`
- `GET /api/wallet/by-telegram/{telegram_id}`
- `GET /api/trade/offers`
- `POST /api/trade/create-offer`
- `POST /telegram/webhook` – Telegram webhook endpoint
