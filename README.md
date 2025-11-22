# SLH Wallet 2.0 – קופת הקהילה + ארנק טלגרם + שוק P2P

פרויקט זה הוא שכבת הארנק והבורסה הקהילתית של **SLHNET**:

- ארנק קהילתי שמנוהל דרך בוט טלגרם (`@Slh_selha_bot`)
- פרופיל ארנק ציבורי באתר (לפי Telegram ID)
- שוק P2P למסחר ב־SLH/BNB בין חברי הקהילה
- חיבור עתידי לטוקן **SLH_TON** (1 SLH_TON = 1000 SLH_BNB)
- API מסודר לבוטים / שירותים חיצוניים

הכל רץ על:

- **FastAPI** (Python)
- **PostgreSQL (Neon)** בתור בסיס נתונים
- **Koyeb** בתור שרת הרצה
- בוט טלגרם דרך Webhook ל־`/telegram/webhook`


---

## 1. מבנה המערכת

### 1.1 רכיבים עיקריים

- `app/main.py` – אפליקציית FastAPI, רישום ראוטרים, סטטיים ותיעוד.
- `app/telegram_bot.py` – בוט טלגרם: `/start`, `/wallet`, `/balances`, `/bank` ועוד.
- `app/models.py` – מודלים של SQLAlchemy (טבלאות `wallets`, `trade_offers`).
- `app/schemas.py` – מודלי Pydantic ל־API.
- `app/database.py` – חיבור ל־PostgreSQL (Neon) דרך SQLAlchemy.
- `app/db_schema.py` – יצירה/עדכון סכימה (DDL) אוטומטית בלי Alembic.
- `app/routers/wallet.py` – REST API לניהול ארנקים.
- `app/routers/trade.py` – REST API להצעות מסחר P2P.
- `frontend/index.html` – דף הבית + שוק P2P.
- `frontend/wallet.html` – פרופיל ארנק לפי Telegram ID (תצוגה בלבד).
- `sql/schema_full.sql` – סכימת DB מלאה (DDL).
- `sql/schema_patch.sql` – פאטצ'ים מצטברים לשדרוג סכימה קיימת.

---

## 2. הסכימה – בסיס הנתונים

### 2.1 טבלת ארנקים `wallets`

שדות עיקריים:

- `telegram_id` (PK) – מזהה יוניק של המשתמש בטלגרם (string).
- `username` – שם משתמש בטלגרם.
- `first_name`, `last_name` – שם פרטי/משפחה.
- `bnb_address` – כתובת BNB / SLH_BNB.
- `slh_address` – כתובת SLH (ב־BNB chain).
- `slh_ton_address` – כתובת SLH_TON (אופציונלי, לעתיד).
- `bank_account_number`, `bank_name` – פרטי בנק לקבלת תשלומים.
- `created_at`, `updated_at` – חותמות זמן.

### 2.2 טבלת הצעות מסחר `trade_offers`

שדות עיקריים:

- `id` – מפתח ראשי (serial).
- `seller_telegram_id` – מוכר.
- `buyer_telegram_id` – קונה (ברגע סגירת העסקה).
- `token_symbol` – לדוגמה `SLH`, `SLH_TON`.
- `amount` – כמות למכירה.
- `price_bnb` – מחיר ליחידה ב־BNB.
- `status` – `ACTIVE` / `FILLED` / `CANCELLED`.
- `created_at`, `updated_at` – חותמות זמן.

> **הערה:** כל ה־DDL המלא נמצא בקובץ `sql/schema_full.sql`.  
> פאטצ'ים תוספתיים מרוכזים ב־`sql/schema_patch.sql`.

---

## 3. איך הסכימה מתעדכנת אוטומטית

במקום Alembic, משתמשים במנגנון פשוט:

- בקובץ `app/db_schema.py` מוגדרות הפקודות ליצירת/עדכון הטבלאות.
- בפונקציה `ensure_schema()` מריצים:
  - את ה־DDL הבסיסי (אם הטבלאות לא קיימות)
  - את ה־patchים המוגדרים.

בקובץ `app/main.py` מתבצעת קריאה ל־`ensure_schema()` בזמן עליית האפליקציה:

```python
from .db_schema import ensure_schema

# ...

# Ensure DB schema (idempotent, safe on each startup)
ensure_schema()
```

המשמעות:  
בכל עליית שרת – אם חסרה עמודה/טבלה, היא תיווצר.  
אם הכל קיים – לא קורה כלום.

---

## 4. זרימת המשתמש – איך הארנק עובד

1. המשתמש נכנס לבוט טלגרם `@Slh_selha_bot` ולוחץ `/start`.
2. הבוט קורא ל־`_ensure_wallet(...)`:
   - בודק אם יש ארנק רשום ב־DB לפי `telegram_id`.
   - אם אין – יוצר שורה בטבלת `wallets`.
3. המשתמש יכול:
   - לעדכן כתובות (BNB / SLH / SLH_TON) דרך פקודות בבוט (לפי מימוש).
   - לעדכן פרטי בנק עם `/bank`.
   - לראות יתרות עם `/balances` (כרגע לוגיקה בסיסית / דמו).
4. באתר:
   - דף `/` מציג את שוק ה־P2P דרך הקריאה `GET /api/trade/offers`.
   - דף `/wallet?telegram_id=XXXXX` מציג פרופיל ארנק ציבורי (read-only):
     - פרטי טלגרם בסיסיים.
     - כתובת BNB/SLH_BNB.
     - כתובת SLH_TON אם קיימת.
   - אין טפסים לשינוי פרטים – הכל מתבצע דרך הבוט.

---

## 5. הגדרות סביבה (ENV)

דוגמה לקובץ `.env` מקומי:

```bash
# FastAPI
ENVIRONMENT=production
LOG_LEVEL=INFO

# Database (Neon)
DATABASE_URL=postgresql+psycopg2://<user>:<password>@<host>/<db>

# Telegram
TELEGRAM_BOT_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TELEGRAM_WEBHOOK_URL=https://thin-charlot-osifungar-d382d3c9.koyeb.app/telegram/webhook

# CORS
CORS_ORIGINS=*

# SLH / TON logic
SLH_TON_FACTOR=1000
```

ב־Koyeb מגדירים את אותם משתנים תחת **Environment**.

---

## 6. הרצה מקומית

```bash
# 1. יצירת וירטואל־env
python -m venv .venv
source .venv/bin/activate  # ב-Windows: .venv\Scripts\activate

# 2. התקנת תלויות
pip install -r requirements.txt

# 3. הגדרת DATABASE_URL (ל-Neon או ל-Postgres מקומי)
export DATABASE_URL=postgresql+psycopg2://...

# 4. הרצת השרת
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

בדיקות:

- `GET http://localhost:8000/health`
- `GET http://localhost:8000/docs`
- `POST http://localhost:8000/api/wallet/register`
- `GET http://localhost:8000/api/trade/offers`

---

## 7. פריסה ל-Koyeb

1. דוחפים את הקוד ל־GitHub: `osifeu-prog/SLH_Wallet`.
2. ב-Koyeb:
   - יוצרים שירות Web חדש מה־repo.
   - Port פנימי: `8000`.
   - פקודת הרצה (Procfile או Buildpack):
     - `web: uvicorn app.main:app --host 0.0.0.0 --port 8000`
3. מגדירים Environment:
   - `DATABASE_URL` (Neon).
   - `TELEGRAM_BOT_TOKEN`.
   - `TELEGRAM_WEBHOOK_URL`.
   - שאר ה־ENV הדרושים.
4. אחרי שהשירות עולה ו־`/health` מחזיר `{"status": "ok"}`, מגדירים Webhook לטלגרם:
   - או דרך ה־קוד (אם כבר מובנה),
   - או ידנית עם קריאה ל-`https://api.telegram.org/bot<token>/setWebhook?...`.

---

## 8. בדיקות זרימה (QA בסיסי)

1. **בדיקת בריאות**
   - פותחים `https://<app-url>/health` – צריך לקבל `{"status": "ok"}`.

2. **בדיקת פתיחת ארנק**
   - שולחים `/start` לבוט.
   - מצפים להודעת ברוך הבא + קישור לארנק.

3. **בדיקת פרופיל ארנק באתר**
   - פותחים את הקישור שקיבלת בבוט, לדוגמה:
     - `https://<app-url>/wallet?telegram_id=224223270`
   - רואים פרטי ארנק (גם אם רק BNB address קיימת).

4. **יצירת הצעת מכירה P2P**
   - דרך Swagger: `POST /api/trade/create-offer`.
   - מציינים:
     - `telegram_id` של מוכר.
     - `token_symbol=SLH`.
     - `amount`.
     - `price_bnb`.
   - בודקים שההצעה מופיעה בדף הראשי (`/`).

5. **עדכון סכימה אחרי שינויי קוד**
   - פשוט עושים redeploy.
   - `ensure_schema()` ירוץ ויוודא שהעמודות החדשות קיימות.

---

## 9. סיבוב מפתחות (Key Rotation) – תזכורת

מומלץ להחליף מפתחות (ארנק חוזה / BSC / TON או טוקן BOT של טלגרם) באופן תקופתי.

### 9.1 צעדים כלליים

1. מייצרים מפתח/ארנק חדש במקום בטוח.
2. מעדכנים את ה־ENV (למשל ב-Koyeb / Neon).
3. מבצעים redeploy לשירות.
4. שומרים תיעוד קצר (תאריך, סיבה, מי ביצע).

### 9.2 דוגמה ל-PowerShell (לשימוש מקומי/תזכורת)

```powershell
# עדכון TOKEN בקובץ .env מקומי
(Get-Content ".env") `
  -replace "TELEGRAM_BOT_TOKEN=.*", "TELEGRAM_BOT_TOKEN=NEW_TOKEN_HERE" `
  | Set-Content ".env"

# בדיקת הקובץ
Get-Content ".env" | Select-String "TELEGRAM_BOT_TOKEN"

# Commit + push
git add .env
git commit -m "chore: rotate telegram bot token"
git push
```

> ב-Koyeb מעדכנים את ה-Environment דרך ה-UI או ה-CLI, ואז לוחצים Redeploy.

---

## 10. המשך פיתוח

- הוספת שדות מתקדמים לארנק (NFT, סטייקינג).
- הרחבת שוק P2P:
  - סטטוסי עסקה מפורטים,
  - לוגיקה של התאמת קונים/מוכרים,
  - webhooks לאישור תשלומים.
- אינטגרציה עמוקה עם **TON**:
  - קריאה ל-API של TON לפי ה-API KEY שלך.
  - חישוב חלוקת ג'טונים SLH_TON מול SLH_BNB.
- שכבת **Academy**:
  - מודול קורסים, שיעורים ומדדי פעילות,
  - חיבור ישיר לתגמול ב-SLH.

---

כל הקוד כאן נבנה כך שתוכל:

1. לדחוף אותו ישירות ל-GitHub.
2. לחבר אותו ל-Koyeb.
3. לנהל את הקהילה שלך דרך טלגרם, עם אתר אחד מרכזי שמסביר, מציג את השוק ומספק תצוגת ארנק.

בהצלחה 🚀  
SLH Wallet 2.0 – שכבת הכלכלה הקהילתית שלך.
