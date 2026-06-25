-- Vanchai SEO Engine — SQLite Schema
-- Run: sqlite3 db/seo_engine.db < db/schema.sql

-- Products: mirrors the CSV columns produced by xlsx_to_csv.py
CREATE TABLE IF NOT EXISTS products (
    id                     INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_article_number  TEXT    NOT NULL,
    vendor_article_name    TEXT    NOT NULL,
    material               TEXT,
    product_details        TEXT,
    product_type           TEXT,
    amazon_url             TEXT,
    myntra_url             TEXT,
    nykaa_url              TEXT,
    wix_url                TEXT,
    image_url              TEXT,
    price                  TEXT,
    category               TEXT,
    category_url           TEXT,
    json_ld                TEXT,
    created_at             TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at             TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (vendor_article_number, vendor_article_name)
);

-- Keyword-product pairs: only rows with validated=1 may be generated
CREATE TABLE IF NOT EXISTS keyword_product_pairs (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id        INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    keyword           TEXT    NOT NULL,
    modifier          TEXT    NOT NULL,
    slug              TEXT    NOT NULL,
    search_volume     INTEGER NOT NULL DEFAULT 0,
    validated         INTEGER NOT NULL DEFAULT 0,  -- 1 = passed ≥100 searches/month gate
    validation_source TEXT,                        -- 'dataforseo' | 'manual'
    validated_at      TEXT,
    created_at        TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (slug)
);

-- Generated pages: one row per published HTML file
CREATE TABLE IF NOT EXISTS generated_pages (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    pair_id          INTEGER NOT NULL REFERENCES keyword_product_pairs(id) ON DELETE CASCADE,
    slug             TEXT    NOT NULL UNIQUE,
    status           TEXT    NOT NULL DEFAULT 'pending',  -- pending | approved | review_queue | blocked
    seo_score        INTEGER,
    uniqueness_score REAL,
    word_count       INTEGER,
    html_path        TEXT,
    gate_results     TEXT,  -- JSON: {gate_name: pass/fail}
    generated_at     TEXT   NOT NULL DEFAULT (datetime('now')),
    last_updated     TEXT   NOT NULL DEFAULT (datetime('now'))
);

-- Review queue: pages that failed one recoverable gate, awaiting human decision
CREATE TABLE IF NOT EXISTS review_queue (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    page_id        INTEGER NOT NULL REFERENCES generated_pages(id) ON DELETE CASCADE,
    slug           TEXT    NOT NULL,
    reason         TEXT    NOT NULL,
    gate_results   TEXT,           -- JSON
    queued_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    reviewed_at    TEXT,
    review_action  TEXT            -- 'approved' | 'discarded'
);

-- Keyword registry: enforces one slug per keyword across all products
CREATE TABLE IF NOT EXISTS keyword_registry (
    slug          TEXT    PRIMARY KEY,
    keyword       TEXT    NOT NULL,
    pair_id       INTEGER REFERENCES keyword_product_pairs(id) ON DELETE SET NULL,
    registered_at TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Indexes for hot paths
CREATE INDEX IF NOT EXISTS idx_pairs_validated ON keyword_product_pairs (validated);
CREATE INDEX IF NOT EXISTS idx_pairs_product   ON keyword_product_pairs (product_id);
CREATE INDEX IF NOT EXISTS idx_pages_status    ON generated_pages (status);
CREATE INDEX IF NOT EXISTS idx_queue_reviewed  ON review_queue (reviewed_at);
