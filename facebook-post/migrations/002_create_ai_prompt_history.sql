-- Migration: create ai_prompt_history table
CREATE TABLE IF NOT EXISTS ai_prompt_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    itemid TEXT NOT NULL,
    prompt TEXT NOT NULL,
    response TEXT,
    error_message TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY(itemid) REFERENCES shopee_affiliate_cards(itemid)
);
CREATE INDEX IF NOT EXISTS idx_prompt_history_itemid ON ai_prompt_history(itemid);
