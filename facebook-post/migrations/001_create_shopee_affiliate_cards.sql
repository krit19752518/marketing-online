-- Migration: create shopee_affiliate_cards table
CREATE TABLE IF NOT EXISTS shopee_affiliate_cards (
    itemid TEXT PRIMARY KEY,
    title TEXT,
    price REAL,
    sale_price REAL,
    discount_percentage REAL,
    stock INTEGER,
    item_sold INTEGER,
    item_rating REAL,
    likes_count INTEGER,
    is_official_shop INTEGER DEFAULT 0,
    is_preferred_shop INTEGER DEFAULT 0,
    has_lowest_price_guarantee INTEGER DEFAULT 0,
    product_link TEXT,
    product_short_link TEXT,
    image_link TEXT,
    description TEXT,
    status TEXT DEFAULT 'new',
    ai_prompt TEXT,
    ai_caption TEXT,
    reviewer_note TEXT,
    assigned_to TEXT,
    source_filename TEXT,
    feed_date TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_shopee_status ON shopee_affiliate_cards(status);
CREATE INDEX IF NOT EXISTS idx_shopee_discount ON shopee_affiliate_cards(discount_percentage);
CREATE INDEX IF NOT EXISTS idx_shopee_updated ON shopee_affiliate_cards(updated_at);
