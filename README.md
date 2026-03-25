# Real-Time Commodity Price Analytics Pipeline

End-to-end streaming pipeline that ingests live commodity prices from Yahoo Finance, processes them through Apache Kafka and Apache Flink for real-time analytics (SMA-20), persists results to PostgreSQL, and serves them to a dashboard.

## Architecture

```
Yahoo Finance API
       │
       ▼
  Python Producers ──► Kafka Topics ──► Flink SQL ──► PostgreSQL
  (GC=F, SI=F,         (gold_prices,    (SMA-20       (permanent
   CL=F, DX-Y.NYB)      silver_prices,   windowed      storage,
                         oil_prices,      aggregation)  queryable)
                         usd_prices)
```

## Tech Stack

| Component     | Technology                      | Purpose                            |
|---------------|---------------------------------|------------------------------------|
| Ingestion     | Python 3 + `yfinance`           | Fetch live prices every 10s        |
| Messaging     | Apache Kafka 7.5.0              | Decoupled event streaming          |
| Processing    | Apache Flink 1.18 (SQL)         | Stateful windowed aggregation      |
| Storage       | PostgreSQL 16                   | Persistent analytics results       |
| Monitoring    | Kafdrop                         | Kafka topic inspection UI          |
| Orchestration | Docker Compose                  | Single-command infrastructure      |

## Quick Start

```bash
# 1. Start infrastructure
docker compose up -d

# 2. Activate Python environment
.\venv\Scripts\Activate.ps1          # Windows
source venv/bin/activate             # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start live producers (one per terminal)
python src/ingestion/commodity_producer.py --ticker GC=F
python src/ingestion/commodity_producer.py --ticker SI=F
python src/ingestion/commodity_producer.py --ticker CL=F
python src/ingestion/commodity_producer.py --ticker DX-Y.NYB

# 5. Open Flink SQL client and load table definitions
docker exec -it flink-jobmanager ./bin/sql-client.sh -i /opt/flink/sql/create_tables.sql

# 6. Start the analytics job (inside Flink SQL)
INSERT INTO gold_analytics_db
SELECT
    ticker,
    `timestamp` AS event_timestamp,
    `open` AS open_price,
    high AS high_price,
    low AS low_price,
    `close` AS close_price,
    volume,
    AVG(`close`) OVER (
        ORDER BY event_time
        RANGE BETWEEN INTERVAL '19' HOUR PRECEDING AND CURRENT ROW
    ) AS sma_20
FROM gold_prices;
```

## Project Structure

```
src/
  ingestion/             # Kafka producers and consumers
    config.py            # Shared settings (broker, tickers, topics)
    commodity_producer.py   # Live price streamer (parameterized by ticker)
    commodity_backfill.py   # Historical data loader (2yr hourly)
    commodity_consumer.py   # Data verification consumer
  processing/            # Flink SQL table definitions
    create_tables.sql    # Source/sink table DDL for Flink
  storage/               # Database initialization
    init.sql             # PostgreSQL schema setup
docs/                    # Reference documentation
external_libs/           # Flink JDBC/Postgres connector JARs (not tracked in git)
docker-compose.yml       # Infrastructure definition
.env.example             # Environment variable template
```

## Configuration

Copy `.env.example` to `.env` and fill in your PostgreSQL credentials before starting:

```bash
cp .env.example .env
```

## Key Design Decisions

- **Event-time processing**: Flink uses `WATERMARK` on the event timestamp, not wall-clock time. This handles late-arriving data and keeps calculations accurate regardless of network latency.
- **Stateful windowing**: The SMA-20 uses `RANGE BETWEEN INTERVAL '19' HOUR PRECEDING`, meaning Flink maintains a rolling window of price data in memory. Checkpointing (every 10 min) persists this state to disk for crash recovery.
- **Decoupled producers**: One generic `commodity_producer.py` handles all tickers via `argparse`. Adding a new commodity requires only a config entry — no code changes.
- **Multi-layer fallback**: The producer tries `fast_info` → `history()` → `info` when fetching prices, ensuring resilience against Yahoo Finance API instability.

## Monitoring

| Service    | URL                        |
|------------|----------------------------|
| Kafdrop    | http://localhost:9000      |
| Flink UI   | http://localhost:8081      |
| PostgreSQL | `localhost:5432`           |
