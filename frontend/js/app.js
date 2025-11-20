const API_BASE = window.location.origin;

async function registerWallet() {
  const telegram_id = document.getElementById("tg-id").value;
  const bnb_address = document.getElementById("bnb-address").value;
  const slh_address = document.getElementById("slh-address").value;

  const res = await fetch(API_BASE + "/api/wallet/register", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ telegram_id, bnb_address, slh_address })
  });
  const data = await res.json();
  document.getElementById("wallet-result").textContent = JSON.stringify(data, null, 2);
}

async function fetchWallet() {
  const telegram_id = document.getElementById("tg-id").value;
  const res = await fetch(API_BASE + "/api/wallet/by-telegram/" + telegram_id);
  const data = await res.json();
  document.getElementById("wallet-result").textContent = JSON.stringify(data, null, 2);
}

async function loadOffers() {
  const res = await fetch(API_BASE + "/api/trade/offers");
  const data = await res.json();
  document.getElementById("offers-result").textContent = JSON.stringify(data, null, 2);
}
