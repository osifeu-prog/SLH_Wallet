# SLH_Wallet_2.0

Unified BNB/SLH wallet + API + basic trading layer + Telegram webhook.

## Key endpoints

- `GET /health` – health check
- `GET /` – basic service info
- `GET /api/meta` – environment & config info
- `POST /api/wallet/register` – register/update wallet for Telegram user
- `GET /api/wallet/by-telegram/{telegram_id}` – fetch wallet by Telegram ID
- `GET /api/trade/offers` – list active trade offers
- `POST /api/trade/create-offer` – create trade offer
- `POST /telegram/webhook` – Telegram webhook endpoint

## Running locally

```bash
pip install -r requirements.txt
bash start.sh
```

Service will run on `http://127.0.0.1:8000`.
