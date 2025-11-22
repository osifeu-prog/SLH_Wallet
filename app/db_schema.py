
from __future__ import annotations

import logging
from textwrap import dedent

from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = logging.getLogger("slh_wallet.db_schema")


DDL_STATEMENTS = [
    # wallets table
    dedent(
        """
        CREATE TABLE IF NOT EXISTS wallets (
            telegram_id VARCHAR(64) PRIMARY KEY,
            username VARCHAR(64),
            first_name VARCHAR(128),
            last_name VARCHAR(128),
            bnb_address VARCHAR(255),
            slh_address VARCHAR(255),
            slh_ton_address VARCHAR(255),
            bank_account_name VARCHAR(255),
            bank_account_number VARCHAR(64),
            internal_slh_balance DOUBLE PRECISION DEFAULT 0,
            internal_slh_locked DOUBLE PRECISION DEFAULT 0,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        """
    ),
    # trade_offers table
    dedent(
        """
        CREATE TABLE IF NOT EXISTS trade_offers (
            id SERIAL PRIMARY KEY,
            seller_telegram_id VARCHAR(64) NOT NULL,
            buyer_telegram_id VARCHAR(64),
            token_symbol VARCHAR(32) NOT NULL DEFAULT 'SLH',
            amount DOUBLE PRECISION NOT NULL,
            price_bnb DOUBLE PRECISION NOT NULL,
            status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        """
    ),
    # internal_transfers table
    dedent(
        """
        CREATE TABLE IF NOT EXISTS internal_transfers (
            id SERIAL PRIMARY KEY,
            from_telegram_id VARCHAR(64) NOT NULL,
            to_telegram_id VARCHAR(64) NOT NULL,
            amount DOUBLE PRECISION NOT NULL,
            memo VARCHAR(255),
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        """
    ),
    # staking_positions table
    dedent(
        """
        CREATE TABLE IF NOT EXISTS staking_positions (
            id SERIAL PRIMARY KEY,
            telegram_id VARCHAR(64) NOT NULL,
            amount_locked DOUBLE PRECISION NOT NULL,
            annual_rate_percent DOUBLE PRECISION NOT NULL DEFAULT 120.0,
            started_at TIMESTAMPTZ DEFAULT NOW(),
            unlock_at TIMESTAMPTZ,
            is_active BOOLEAN NOT NULL DEFAULT TRUE
        );
        """
    ),
    # Make sure extra columns exist in existing DBs (idempotent)
    "ALTER TABLE wallets ADD COLUMN IF NOT EXISTS slh_ton_address VARCHAR(255);",
    "ALTER TABLE wallets ADD COLUMN IF NOT EXISTS bank_account_name VARCHAR(255);",
    "ALTER TABLE wallets ADD COLUMN IF NOT EXISTS bank_account_number VARCHAR(64);",
    "ALTER TABLE wallets ADD COLUMN IF NOT EXISTS internal_slh_balance DOUBLE PRECISION DEFAULT 0;",
    "ALTER TABLE wallets ADD COLUMN IF NOT EXISTS internal_slh_locked DOUBLE PRECISION DEFAULT 0;",
    "ALTER TABLE wallets ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();",
    "ALTER TABLE wallets ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();",
    "ALTER TABLE trade_offers ADD COLUMN IF NOT EXISTS seller_telegram_id VARCHAR(64);",
    "ALTER TABLE trade_offers ADD COLUMN IF NOT EXISTS buyer_telegram_id VARCHAR(64);",
    "ALTER TABLE trade_offers ADD COLUMN IF NOT EXISTS status VARCHAR(32) DEFAULT 'ACTIVE';",
    "ALTER TABLE trade_offers ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();",
]


def ensure_schema(engine: Engine) -> None:
    logger.info("Ensuring DB schema is up-to-date...")
    with engine.begin() as conn:
        for ddl in DDL_STATEMENTS:
            try:
                conn.execute(text(ddl))
            except Exception as e:  # noqa: BLE001
                logger.warning("DDL failed (but continuing): %s", e)
    logger.info("DB schema ensured.")
