-- sql/schema_full.sql
-- Full DDL schema for SLH_Wallet community exchange

CREATE TABLE IF NOT EXISTS wallets (
    telegram_id           VARCHAR(64) PRIMARY KEY,
    username              VARCHAR(64),
    first_name            VARCHAR(128),
    last_name             VARCHAR(128),
    bnb_address           VARCHAR(255),
    slh_address           VARCHAR(255),
    slh_ton_address       VARCHAR(255),
    bank_account_number   VARCHAR(255),
    bank_account_name     VARCHAR(255),
    created_at            TIMESTAMPTZ DEFAULT NOW(),
    updated_at            TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS trade_offers (
    id                    SERIAL PRIMARY KEY,
    -- P2P seller / buyer on Telegram
    seller_telegram_id    VARCHAR(64) NOT NULL,
    buyer_telegram_id     VARCHAR(64),
    token_symbol          VARCHAR(32) NOT NULL, -- 'SLH_BNB' / 'SLH_TON'
    amount                NUMERIC(36, 18) NOT NULL,
    price_bnb             NUMERIC(36, 18) NOT NULL,
    status                VARCHAR(32) NOT NULL DEFAULT 'ACTIVE', -- ACTIVE / FILLED / CANCELLED
    created_at            TIMESTAMPTZ DEFAULT NOW(),
    updated_at            TIMESTAMPTZ DEFAULT NOW()
);

-- Optional simple referral ledger (bonus in SLH_TON units)
CREATE TABLE IF NOT EXISTS referrals (
    id                    SERIAL PRIMARY KEY,
    referrer_telegram_id  VARCHAR(64) NOT NULL,
    referred_telegram_id  VARCHAR(64) NOT NULL,
    reward_slh_ton        NUMERIC(36, 18) NOT NULL DEFAULT 0,
    created_at            TIMESTAMPTZ DEFAULT NOW()
);
