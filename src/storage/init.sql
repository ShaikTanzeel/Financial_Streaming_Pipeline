-- init.sql
-- This script runs once when the PostgreSQL container starts for the first time.

-- Create the table structure to hold our processed SMA analytics
CREATE TABLE IF NOT EXISTS gold_analytics (
    ticker VARCHAR(20),
    event_timestamp VARCHAR(50), -- Using string to keep it simple with Flink's STRING output
    open_price DOUBLE PRECISION,
    high_price DOUBLE PRECISION,
    low_price DOUBLE PRECISION,
    close_price DOUBLE PRECISION,
    volume BIGINT,
    sma_20 DOUBLE PRECISION,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Record when Postgres actually received the data
);

-- Index the ticker and timestamp for faster querying later in Phase 3
CREATE INDEX idx_gold_ticker ON gold_analytics(ticker);
CREATE INDEX idx_gold_timestamp ON gold_analytics(event_timestamp);
