// app.js - JavaScript משופר עם תמיכה ב-MetaMask

// משתנים גלובליים
let currentAccount = null;

// ✅ בדיקת חיבור MetaMask
async function checkMetaMaskConnection() {
    if (typeof window.ethereum !== 'undefined') {
        try {
            const accounts = await window.ethereum.request({ 
                method: 'eth_accounts' 
            });
            if (accounts.length > 0) {
                currentAccount = accounts[0];
                updateUIWithMetaMask(currentAccount);
                return true;
            }
        } catch (error) {
            console.error('Error checking MetaMask connection:', error);
        }
    }
    return false;
}

// ✅ עדכון UI עם נתוני MetaMask
function updateUIWithMetaMask(account) {
    // עדכון שדות אוטומטית אם קיימים
    const bnbInput = document.getElementById('bnb_address');
    const slhInput = document.getElementById('slh_address');
    
    if (bnbInput) bnbInput.value = account;
    if (slhInput) slhInput.value = account;
    
    // הצגת הודעה למשתמש
    showNotification('MetaMask מחובר: ' + account.slice(0, 6) + '...' + account.slice(-4), 'success');
}

// ✅ הצגת התראות
function showNotification(message, type = 'info') {
    // ניתן להוסיף כאן לוגיקה להצגת התראות יפות
    console.log(`${type.toUpperCase()}: ${message}`);
    
    // הצגה בסיסית - ניתן לשפר עם Toast library
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        border-radius: 8px;
        color: white;
        z-index: 1000;
        font-weight: 500;
        max-width: 300px;
    `;
    
    if (type === 'success') {
        notification.style.background = '#22c55e';
    } else if (type === 'error') {
        notification.style.background = '#ef4444';
    } else {
        notification.style.background = '#2563eb';
    }
    
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        document.body.removeChild(notification);
    }, 5000);
}

// ✅ טעינת מידע כללי
async function fetchMeta() {
  try {
    const res = await fetch('/api/meta');
    const data = await res.json();
    const metaElement = document.getElementById('meta-info');
    
    if (metaElement) {
      metaElement.textContent =
        'ENV: ' + data.env +
        ' | DB: ' + data.db_url_prefix +
        ' | Bot: ' + (data.bot_url || 'N/A') +
        ' | Security: ' + (data.security?.cors_restricted ? '✅' : '❌');
    }
  } catch (e) {
    console.error('Error loading service info:', e);
    const metaElement = document.getElementById('meta-info');
    if (metaElement) {
      metaElement.textContent = 'שגיאה בטעינת מידע השירות';
    }
  }
}

// ✅ רישום ארנק (גיבוי ל-API הישן)
async function registerWallet(e) {
  e.preventDefault();
  const body = {
    telegram_id: document.getElementById('telegram_id').value,
    username: document.getElementById('username').value || null,
    first_name: document.getElementById('first_name').value || null,
    bnb_address: document.getElementById('bnb_address').value || null,
    slh_address: document.getElementById('slh_address').value || null,
  };
  
  try {
    const res = await fetch('/api/wallet/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    
    const data = await res.json();
    const resultElement = document.getElementById('wallet-result');
    
    if (resultElement) {
      resultElement.textContent = JSON.stringify(data, null, 2);
    }
    
    if (res.ok) {
      showNotification('ארנק נרשם בהצלחה!', 'success');
    } else {
      showNotification('שגיאה ברישום: ' + (data.detail || 'Unknown error'), 'error');
    }
  } catch (e) {
    console.error('Wallet registration error:', e);
    showNotification('שגיאת רשת: ' + e.message, 'error');
  }
}

// ✅ יצירת הצעת מסחר
async function createOffer(e) {
  e.preventDefault();
  const params = new URLSearchParams({
    telegram_id: document.getElementById('trade_telegram_id').value,
    token_symbol: document.getElementById('token_symbol').value,
    amount: document.getElementById('amount').value,
    price_bnb: document.getElementById('price_bnb').value,
  });
  
  try {
    const res = await fetch('/api/trade/create-offer?' + params.toString(), {
      method: 'POST',
    });
    
    const data = await res.json();
    const resultElement = document.getElementById('trade-result');
    
    if (resultElement) {
      resultElement.textContent = JSON.stringify(data, null, 2);
    }
    
    if (res.ok) {
      showNotification('הצעת מסחר נוצרה בהצלחה!', 'success');
    } else {
      showNotification('שגיאה ביצירת הצעה: ' + (data.detail || 'Unknown error'), 'error');
    }
  } catch (e) {
    console.error('Trade offer creation error:', e);
    showNotification('שגיאת רשת: ' + e.message, 'error');
  }
}

// ✅ טעינת הצעות מסחר
async function loadOffers() {
  try {
    const res = await fetch('/api/trade/offers');
    const data = await res.json();
    const resultElement = document.getElementById('trade-result');
    
    if (resultElement) {
      resultElement.textContent = JSON.stringify(data, null, 2);
    }
    
    showNotification(`נטענו ${data.length} הצעות מסחר`, 'success');
  } catch (e) {
    console.error('Error loading offers:', e);
    showNotification('שגיאה בטעינת הצעות: ' + e.message, 'error');
  }
}

// ✅ בדיקת יתרות
async function checkBalances(telegramId) {
  try {
    const res = await fetch(`/api/wallet/${telegramId}/balances`);
    const data = await res.json();
    
    if (data.success) {
      return {
        bnb: data.bnb_balance,
        slh: data.slh_balance,
        address: data.bnb_address
      };
    } else {
      throw new Error('Failed to fetch balances');
    }
  } catch (e) {
    console.error('Error checking balances:', e);
    throw e;
  }
}

// ✅ אתחול האפליקציה
async function initializeApp() {
  // טעינת מידע כללי
  await fetchMeta();
  
  // בדיקת חיבור MetaMask
  await checkMetaMaskConnection();
  
  // רישום event listeners
  const walletForm = document.getElementById('wallet-form');
  if (walletForm) {
    walletForm.addEventListener('submit', registerWallet);
  }
  
  const tradeForm = document.getElementById('trade-form');
  if (tradeForm) {
    tradeForm.addEventListener('submit', createOffer);
  }
  
  const loadOffersBtn = document.getElementById('load-offers');
  if (loadOffersBtn) {
    loadOffersBtn.addEventListener('click', loadOffers);
  }
  
  // האזנה לשינויים ב-MetaMask
  if (typeof window.ethereum !== 'undefined') {
    window.ethereum.on('accountsChanged', (accounts) => {
      if (accounts.length === 0) {
        showNotification('MetaMask נותק', 'error');
        currentAccount = null;
      } else {
        currentAccount = accounts[0];
        updateUIWithMetaMask(currentAccount);
      }
    });
    
    window.ethereum.on('chainChanged', (chainId) => {
      // רענון הדף כאשר המשתמש מחליף רשת
      window.location.reload();
    });
  }
}

// ✅ הרצה כאשר הדף נטען
window.addEventListener('DOMContentLoaded', initializeApp);

// ✅ הפונקציות זמינות globally לנוחיות
window.app = {
  checkMetaMaskConnection,
  showNotification,
  checkBalances,
  registerWallet,
  createOffer,
  loadOffers
};
