"""Lightweight schema management for SLH_Wallet.

This module:
- Creates core tables if they do not exist.
- Adds critical columns (SLH_TON address, P2P seller/buyer, status) if missing.
It is idempotent and safe to run on every startup.
"""

import logging
from sqlalchemy import text

from .database import Base, engine

log = logging.getLogger("slh_wallet.schema")


def ensure_schema() -> None:
    """Create tables via SQLAlchemy and patch columns via raw SQL.

    Safe to call on every startup.
    """
    # 1) Let SQLAlchemy create any missing tables that exist in models.py
    Base.metadata.create_all(bind=engine)

    # 2) Apply PostgreSQL-specific patch for extra columns we rely on
    ddl = """-- sql/schema_patch.sql
-- Non-destructive schema patch to align an existing database with the current models.
-- Safe to run multiple times.

-- wallets: add SLH_TON address if missing
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'wallets' AND column_name = 'slh_ton_address'
    ) THEN
        ALTER TABLE wallets ADD COLUMN slh_ton_address VARCHAR(255);
    END IF;
END$$;

-- trade_offers: add seller/buyer/status if missing
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'trade_offers' AND column_name = 'seller_telegram_id'
    ) THEN
        ALTER TABLE trade_offers ADD COLUMN seller_telegram_id VARCHAR(64);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'trade_offers' AND column_name = 'buyer_telegram_id'
    ) THEN
        ALTER TABLE trade_offers ADD COLUMN buyer_telegram_id VARCHAR(64);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'trade_offers' AND column_name = 'status'
    ) THEN
        ALTER TABLE trade_offers ADD COLUMN status VARCHAR(32) DEFAULT 'ACTIVE';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'trade_offers' AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE trade_offers ADD COLUMN updated_at TIMESTAMPTZ DEFAULT NOW();
    END IF;
END$$;
"""
    with engine.begin() as conn:
        log.info("Running schema_patch.sql to align database schema…")
        conn.exec_driver_sql(ddl)
        log.info("Schema patch completed successfully.")
