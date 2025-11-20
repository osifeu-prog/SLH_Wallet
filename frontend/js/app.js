
async function fetchMeta() {
  try {
    const res = await fetch('/api/meta');
    const data = await res.json();
    document.getElementById('meta-info').textContent =
      'ENV: ' + data.env +
      ' | DB: ' + data.db_url_prefix +
      ' | Bot: ' + (data.bot_url || 'N/A');
  } catch (e) {
    document.getElementById('meta-info').textContent = 'שגיאה בטעינת מידע השירות';
  }
}

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
    document.getElementById('wallet-result').textContent = JSON.stringify(data, null, 2);
  } catch (e) {
    document.getElementById('wallet-result').textContent = 'שגיאה: ' + e;
  }
}

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
    document.getElementById('trade-result').textContent = JSON.stringify(data, null, 2);
  } catch (e) {
    document.getElementById('trade-result').textContent = 'שגיאה: ' + e;
  }
}

async function loadOffers() {
  try {
    const res = await fetch('/api/trade/offers');
    const data = await res.json();
    document.getElementById('trade-result').textContent = JSON.stringify(data, null, 2);
  } catch (e) {
    document.getElementById('trade-result').textContent = 'שגיאה: ' + e;
  }
}

window.addEventListener('DOMContentLoaded', () => {
  fetchMeta();
  document.getElementById('wallet-form').addEventListener('submit', registerWallet);
  document.getElementById('trade-form').addEventListener('submit', createOffer);
  document.getElementById('load-offers').addEventListener('click', loadOffers);
});
