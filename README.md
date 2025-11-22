# SLH_Wallet_2.1 – Core Identity = Telegram + Wallet

מערכת ארנק קהילתית ל-SLH שמבוססת על:

- Telegram ID
- כתובת BNB (BSC)
- כתובת TON (SLH על TON)

אין סיסמאות, אין טפסים רגישים באתר – כל הפעולות הקריטיות נעשות דרך בוט הטלגרם.

---

## 1. מבנה הפרויקט

- `app/`
  - `main.py` – אפליקציית FastAPI, בריאות, מסלולי HTML ו-API (`/u/{telegram_id}`, `/api/...`)
  - `models.py` – מודלי SQLAlchemy כולל:
    - `Wallet` עם השדות:
      - `telegram_id` (PK)
      - `username`, `first_name`, `last_name`
      - `bnb_address`
      - `slh_address`
      - `slh_ton_address` ✅
      - שדות מטא של יצירה/עדכון
    - `TradeOffer` – מודול מסחר פנימי:
      - `seller_telegram_id`, `buyer_telegram_id`
      - `token_symbol`, `amount`, `price_bnb`
      - `status` (ACTIVE / COMPLETED / CANCELLED)
      - `is_active` (לתאימות לאחור)
      - `created_at`, `updated_at`
  - `database.py` – SessionLocal + Base
  - `db_schema.py` – וידוא סכימה אוטומטי (DDL-on-startup)
  - `telegram_bot.py` – בוט SLH:
    - `/start`
    - `/wallet`
    - `/balances`
    - `/bank`
    - `/set_bnb`
    - `/set_ton`
  - `config.py` – הגדרות (pydantic Settings) מתוך משתני סביבה

- `frontend/`
  - `index.html` – דף נחיתה כללי
  - `wallet.html` – דף הסבר: כל הניהול דרך הבוט (לא רושמים כתובות כאן)
  - בעת גלישה ל-`/u/{telegram_id}` נוצר דף HTML דינמי (באמצעות `HTMLResponse`) שמציג:
    - פרטי משתמש
    - כתובות BNB / SLH / SLH_TON
    - יתרות on-chain (אם קיימות)
    - QR להזמנת חברים דרך הבוט

- `static/css/style.css` – עיצוב מודרני לכרטיס האישי

- `start.sh` – נקודת כניסה (Koyeb)
- `requirements.txt` – תלות Python
- `README.md` – קובץ זה

---

## 2. משתני סביבה חשובים (Koyeb / מקומי)

יש להגדיר:

```bash
ENV=production

BASE_URL="https://thin-charlot-osifungar-d382d3c9.koyeb.app"
FRONTEND_API_BASE="https://thin-charlot-osifungar-d382d3c9.koyeb.app"

TELEGRAM_BOT_TOKEN="xxx"
BOT_USERNAME="Slh_selha_bot"

COMMUNITY_LINK="https://t.me/+HIzvM8sEgh1kNWY0"
FRONTEND_BOT_URL="https://t.me/Slh_selha_bot"

DATABASE_URL="postgresql://...neon.../neondb?sslmode=require"

BSC_RPC_URL="https://bsc-dataseed.binance.org/"
BSCSCAN_API_KEY="...optional ליתרות"

SLH_TOKEN_ADDRESS="0xACb0A09414CEA1C879c67bB7A877E4e19480f022"
SLH_TON_FACTOR=1000
SECRET_KEY="some-random-secret"
PAYMENT_METHODS='["BNB","SLH","CREDIT_CARD","BANK_TRANSFER"]'
ADMIN_LOG_CHAT_ID="-1001748319682"
```

---

## 3. זרימת משתמש – TL;DR

1. משתמש שולח `/start` לבוט.
2. הבוט רושם אותו בטבלת `wallets` (אם לא קיים).
3. המשתמש משלם 39 ₪ (מחוץ למערכת) ושולח צילום / אישור → זה נרשם ל-`ADMIN_LOG_CHAT_ID`.
4. אדמין מאשר את המשתמש (מימוש מלא אפשר להוסיף בהמשך – כרגע הליבה מוכנה).
5. המשתמש שולח:
   - `/set_bnb <כתובת_BNB>`
   - `/set_ton <כתובת_TON>`
6. הבוט מעדכן את רשומת הארנק ב-DB.
7. הבוט מחזיר למשתמש קישור אישי:
   - `https://thin-charlot-osifungar-d382d3c9.koyeb.app/u/{telegram_id}`
8. בדפדפן, המשתמש רואה:
   - פרטי טלגרם
   - כתובות ארנק
   - יתרות BNB/SLH (אם זמינות)
   - QR להזמנת חברים → `https://t.me/Slh_selha_bot?start=ref_{telegram_id}`

כל פעולה שקשורה לכסף בפועל (סטייקינג, שינוי פרטי בנק, משיכות) נעשית דרך הבוט – האתר הוא כרטיס אישי/לוח מחוונים.

---

## 4. הרצת הפרויקט מקומית

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt

export ENV=development
export TELEGRAM_BOT_TOKEN="your-bot-token"
export BOT_USERNAME="Slh_selha_bot"
export COMMUNITY_LINK="https://t.me/+HIzvM8sEgh1kNWY0"
export FRONTEND_BOT_URL="https://t.me/Slh_selha_bot"
export DATABASE_URL="postgresql://user:pass@host:port/dbname"

# להרצה:
bash start.sh
# או:
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

בדיקה:

- `http://localhost:8000/health`
- `http://localhost:8000/docs`
- `http://localhost:8000/u/224223270` (לאחר שנוצר משתמש כזה ב-DB)
- קריאה ל-`/telegram/webhook` תתבצע מטלגרם בלבד (Webhook).

---

## 5. וידוא סכימה (DB Schema) ללא Alembic

בעת עליית השרת, `db_schema.ensure_schema_patch()` מריץ DDL:

- וידוא טבלת `wallets`
  - מוסיף `slh_ton_address` אם חסר
- וידוא טבלת `trade_offers`
  - מוסיף `status`
  - מוסיף `seller_telegram_id`
  - מוסיף `buyer_telegram_id`
  - מוסיף `updated_at`

כך שאפילו אם יצרת את הטבלאות ידנית ב-Neon, השרת מיישר את הסכמה בזמן ריצה.

---

## 6. מתי להחליף מפתחות / חוזים?

מומלץ:

- לשמור את כל המפתחות (BSC / TON / SLH) כ-ENV בלבד.
- כאשר מחליפים חוזה SLH:
  - מעדכנים:
    - `SLH_TOKEN_ADDRESS`
    - אם צריך, גם `SLH_TON_FACTOR`
  - מבצעים `git commit` ו-`git push`
  - נותנים ל-Koyeb לפרוס מחדש מה-`main`.

לגבי חשבונות בנק / תשלומי 39 ₪:

- *לעולם לא* לקודד מספרי חשבון ישירות בקוד.
- להציג אותם מה־ENV או מטבלת קונפיגורציה בעתיד.

---

## 7. שלבים להפצה

1. ודא שכל ה-ENV מוגדרים ב-Koyeb (כמו בדוגמה למעלה).
2. ארוז את הפרויקט לקובץ ZIP ודחוף ל-GitHub (`osifeu-prog/SLH_Wallet`).
3. בקויוב:
   - ודא שה-Service מצביע על ה-Repo ועל Branch `main`.
   - ודא שפורט ה-HTTP הוא `8000`.
4. בצע Redeploy.
5. בדוק:
   - שהבוט מקבל `/start` בלי שגיאות בלוגים.
   - שהקריאה ל-`/u/{telegram_id}` עובדת.
   - שאין שגיאות SQL על עמודות חסרות.

מכאן אפשר להמשיך לפתח:

- מודול סטייקינג (טבלאות: `staking_positions`)
- מודול עסקאות פנימיות (טבלת `internal_transfers`)
- דשבורד אדמין מורחב

הפרויקט כפי שהוא כעת נותן לך:

- זהות נקייה: Telegram + ארנק
- כרטיס אישי ו-QR לשיתוף
- בסיס חזק להמשך פיתוח האקוסיסטם (אקדמיה, בורסה, סטייקינג ועוד).
