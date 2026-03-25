-- ==========================================================================
-- Flink SQL: Table Definitions
-- ==========================================================================
-- Run these in the Flink SQL client to connect Flink to Kafka topics.
--
-- These tables are IN-MEMORY only. They disappear when you exit
-- the SQL client or restart Flink. Paste this script each session.
--
-- Usage:
--   1. Open the Flink SQL client:
--      docker exec -it flink-jobmanager ./bin/sql-client.sh
--   2. Paste all the CREATE TABLE statements below.
--   3. Run your queries.
-- ==========================================================================


-- GOLD FUTURES (GC=F)
CREATE TABLE gold_prices (
    ticker STRING,
    `timestamp` STRING,
    `open` DOUBLE,
    high DOUBLE,
    low DOUBLE,
    `close` DOUBLE,
    volume BIGINT,
    source STRING,
    event_time AS TO_TIMESTAMP(REPLACE(SUBSTRING(`timestamp`, 1, 19), 'T', ' ')),
    WATERMARK FOR event_time AS event_time - INTERVAL '5' SECOND
) WITH (
    'connector' = 'kafka',
    'topic' = 'gold_prices',
    'properties.bootstrap.servers' = 'kafka:29092',
    'properties.group.id' = 'flink-gold-reader',
    'scan.startup.mode' = 'earliest-offset',
    'format' = 'json'
);


-- SILVER FUTURES (SI=F)
CREATE TABLE silver_prices (
    ticker STRING,
    `timestamp` STRING,
    `open` DOUBLE,
    day_high DOUBLE,
    day_low DOUBLE,
    price DOUBLE,
    volume BIGINT,
    source STRING,
    event_time AS TO_TIMESTAMP(REPLACE(SUBSTRING(`timestamp`, 1, 19), 'T', ' ')),
    WATERMARK FOR event_time AS event_time - INTERVAL '5' SECOND
) WITH (
    'connector' = 'kafka',
    'topic' = 'silver_prices',
    'properties.bootstrap.servers' = 'kafka:29092',
    'properties.group.id' = 'flink-silver-reader',
    'scan.startup.mode' = 'earliest-offset',
    'format' = 'json'
);


-- CRUDE OIL FUTURES (CL=F)
CREATE TABLE oil_prices (
    ticker STRING,
    `timestamp` STRING,
    `open` DOUBLE,
    day_high DOUBLE,
    day_low DOUBLE,
    price DOUBLE,
    volume BIGINT,
    source STRING,
    event_time AS TO_TIMESTAMP(REPLACE(SUBSTRING(`timestamp`, 1, 19), 'T', ' ')),
    WATERMARK FOR event_time AS event_time - INTERVAL '5' SECOND
) WITH (
    'connector' = 'kafka',
    'topic' = 'oil_prices',
    'properties.bootstrap.servers' = 'kafka:29092',
    'properties.group.id' = 'flink-oil-reader',
    'scan.startup.mode' = 'earliest-offset',
    'format' = 'json'
);


-- US DOLLAR INDEX (DX-Y.NYB)
CREATE TABLE usd_prices (
    ticker STRING,
    `timestamp` STRING,
    `open` DOUBLE,
    day_high DOUBLE,
    day_low DOUBLE,
    price DOUBLE,
    volume BIGINT,
    source STRING,
    event_time AS TO_TIMESTAMP(REPLACE(SUBSTRING(`timestamp`, 1, 19), 'T', ' ')),
    WATERMARK FOR event_time AS event_time - INTERVAL '5' SECOND
) WITH (
    'connector' = 'kafka',
    'topic' = 'usd_prices',
    'properties.bootstrap.servers' = 'kafka:29092',
    'properties.group.id' = 'flink-usd-reader',
    'scan.startup.mode' = 'earliest-offset',
    'format' = 'json'
);

-- ==========================================================================
-- ANALYTICS SINK TABLES (Where Flink writes data back to Kafka)
-- ==========================================================================

-- GOLD ANALYTICS
CREATE TABLE gold_analytics (
    ticker STRING,
    `timestamp` STRING,
    `open` DOUBLE,
    high DOUBLE,
    low DOUBLE,
    `close` DOUBLE,
    volume BIGINT,
    sma_20 DOUBLE
) WITH (
    'connector' = 'kafka',
    'topic' = 'gold_analytics',
    'properties.bootstrap.servers' = 'kafka:29092',
    'format' = 'json'
);

-- ==========================================================================
-- PHASE 2: POSTGRESQL SINK TABLE (Permanent Storage)
-- ==========================================================================

CREATE TABLE gold_analytics_db (
    ticker STRING,
    event_timestamp STRING,
    open_price DOUBLE,
    high_price DOUBLE,
    low_price DOUBLE,
    close_price DOUBLE,
    volume BIGINT,
    sma_20 DOUBLE
) WITH (
    'connector' = 'jdbc',
    'url' = 'jdbc:postgresql://postgres:5432/commodity_analytics',
    'table-name' = 'gold_analytics',
    'username' = 'flink_user',
    'password' = 'flink_password',
    'sink.buffer-flush.max-rows' = '100',
    'sink.buffer-flush.interval' = '2s'
);
