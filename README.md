# SLH_Wallet_2.0

Unified backend + Telegram bot + minimal frontend for SLH Wallet on BNB/SLH.

## Structure

- `app/` – FastAPI backend, database models, Telegram webhook
- `frontend/` – Static pages (`/landing`, `/wallet`)
- `start.sh` – entrypoint (used by Koyeb)
- `requirements.txt` – Python dependencies

## Run locally (dev)

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

export TELEGRAM_BOT_TOKEN="your-bot-token"
export BOT_USERNAME="Slh_selha_bot"
export COMMUNITY_LINK="https://t.me/+HIzvM8sEgh1kNWY0"
# optional DB:
# export DATABASE_URL="postgresql://user:pass@host:port/dbname"

bash start.sh
```

Then open:

- `http://localhost:8000/health`
- `http://localhost:8000/docs`
- `http://localhost:8000/wallet`
```