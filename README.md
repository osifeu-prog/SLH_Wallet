# SLH Community Wallet (BNB Smart Chain)

ארנק קהילתי פשוט לניהול כרטיס משתמש SLH על רשת BNB Smart Chain (BNB + טוקן SLH).

- ללא סיסמאות
- ללא שמירת מפתחות פרטיים
- זהות = טלגרם + כתובת ארנק BNB של המשתמש

## מה המערכת עושה?

1. הבוט בטלגרם יוצר כרטיס משתמש SLH לכל משתתף (`/wallet`).
2. המשתמש מוסיף את כתובת ארנק ה-BNB שלו (`/set_bnb <כתובת_BNB>`).
3. המערכת שומרת במאגר רק:
   - Telegram ID
   - username / שם
   - כתובת BNB (אותה כתובת משמשת גם ל-SLH, כי זה אותו ארנק על BNB Smart Chain).
4. לכל משתמש נוצר כרטיס אישי באתר: `/u/{telegram_id}`
   - מציג Telegram ID ו-username
   - מציג כתובת BNB שלו
   - מציג את כתובת חוזה ה-SLH על BNB
   - מספק QR + קישור לשיתוף כרטיס המשתמש

המסחר והעברות בפועל מתבצעים דרך ארנקי המשתמשים (MetaMask וכד'), לא דרך השרת.

## מבנה הפרויקט

- `app/`
  - `main.py` – FastAPI app, health, static, תיעדוף webhook לבוט
  - `config.py` – הגדרות מתוך ENV
  - `database.py` – חיבור ל-Postgres (Neon)
  - `models.py` – טבלת `wallets` ועוד טבלאות אופציונליות (trade, staking וכו')
  - `db_schema.py` – דואג שהטבלאות קיימות (idempotent)
  - `telegram_bot.py` – בוט SLH הקהילתי (פקודות `/start`, `/wallet`, `/set_bnb`)
  - `routers/wallet.py` – API + תצוגת האזור האישי `/u/{telegram_id}`
- `frontend/`
  - `index.html` – דף נחיתה כללי (אופציונלי)
  - `user.html` – כרטיס משתמש אישי (Identity + כתובת BNB + QR)
  - `user_not_found.html` – למקרה שהמשתמש לא רשום
  - `wallet_redirect.html` – הפניה מ-`/wallet?telegramid=...` ל-`/u/{id}`
  - `wallet_ask_telegram.html` – הסבר להתחיל מהבוט
- `start.sh` – entrypoint ל-Koyeb / הרצה לוקלית
- `requirements.txt` – תלויות Python

## משתני סביבה חשובים

יש להגדיר ב-Koyeb (או בקובץ `.env` ל-local):

```bash
ENV=production

BASE_URL=https://thin-charlot-osifungar-d382d3c9.koyeb.app
FRONTEND_API_BASE=https://thin-charlot-osifungar-d382d3c9.koyeb.app

DATABASE_URL=postgresql://...    # Neon connection string (עם sslmode=require)

TELEGRAM_BOT_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxx
BOT_USERNAME=Slh_selha_bot
COMMUNITY_LINK=https://t.me/+HIzvM8sEgh1kNWY0

BSC_RPC_URL=https://bsc-dataseed.binance.org/
SLH_TOKEN_ADDRESS=0xACb0A09414CEA1C879c67bB7A877E4e19480f022
BSCSCAN_API_KEY=...  # אופציונלי, לשימוש עתידי

PAYMENT_METHODS=["BNB","SLH","CREDIT_CARD","BANK_TRANSFER"]
SECRET_KEY=some-long-random-string
LOG_LEVEL=INFO
```

## הרצה לוקלית (Development)

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt

export ENV=development
export BASE_URL=http://localhost:8000
export FRONTEND_API_BASE=http://localhost:8000
export DATABASE_URL=postgresql://user:pass@localhost:5432/slh_wallet
export TELEGRAM_BOT_TOKEN="your-bot-token"
export BOT_USERNAME="Slh_selha_bot"
export COMMUNITY_LINK="https://t.me/+HIzvM8sEgh1kNWY0"
export BSC_RPC_URL="https://bsc-dataseed.binance.org/"
export SLH_TOKEN_ADDRESS="0xACb0A09414CEA1C879c67bB7A877E4e19480f022"
export SECRET_KEY="dev-secret"

# יצירת סכימה בסיסית ב-DB (טבלת wallets וכו')
python -m app.ensure_schema

# הרצת השרת
bash start.sh
```

ואז לפתוח:

- `http://localhost:8000/health`
- `http://localhost:8000/docs`
- `http://localhost:8000/u/{telegram_id}`

## חיבור הבוט ב-Telegram

1. הגדר ב-BotFather את `WEBHOOK` לכתובת:

   `https://thin-charlot-osifungar-d382d3c9.koyeb.app/telegram/webhook`

2. ודא שהבוט מחובר עם `TELEGRAM_BOT_TOKEN` זהה לזה שבשרת.

3. שלח לעצמך `/start` ואז `/wallet` בבוט.

4. הגדר כתובת BNB שלך:

   ```
   /set_bnb 0xYourBnbAddressHere
   ```

5. פתח בדפדפן:

   ```
   https://thin-charlot-osifungar-d382d3c9.koyeb.app/u/{telegram_id שלך}
   ```

   שם תראה את כתובת ה-BNB שלך + חוזה ה-SLH + QR לשיתוף.

## החלפת מפתחות / חוזה SLH בעתיד

כאשר תרצה להחליף:

- מפתח בוט – עדכן את `TELEGRAM_BOT_TOKEN` ב-Koyeb + BotFather והפעל מחדש את השירות.
- כתובת חוזה SLH – עדכן את `SLH_TOKEN_ADDRESS` ב-Koyeb והפעל מחדש.
- כתובת BASE_URL – עדכן `BASE_URL` + `FRONTEND_API_BASE` יחד.

אין צורך לשנות נתוני משתמשים ב-DB, כל עוד Telegram ID שלהם נשאר זהה.
