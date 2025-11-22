-- sql/schema_patch.sql
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
