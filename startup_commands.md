# Startup Commands

## Start Infrastructure
```powershell
docker compose up -d
```

## Activate Python Environment
```powershell
.\venv\Scripts\Activate.ps1
```

## Start Live Producers
Open 4 separate terminals, activate the venv in each, and run one per terminal:
```powershell
python src/ingestion/commodity_producer.py --ticker GC=F
```
```powershell
python src/ingestion/commodity_producer.py --ticker SI=F
```
```powershell
python src/ingestion/commodity_producer.py --ticker CL=F
```
```powershell
python src/ingestion/commodity_producer.py --ticker DX-Y.NYB
```

## Open Flink SQL Client and Load Tables
This opens the Flink SQL shell and pre-loads all table definitions from `create_tables.sql`:
```powershell
docker exec -it flink-jobmanager ./bin/sql-client.sh -i /opt/flink/sql/create_tables.sql
```

## Start the Flink Analytics Job
Paste this inside the Flink SQL prompt to start the SMA-20 calculation and write results to PostgreSQL:
```sql
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

## Verify Data in PostgreSQL
```powershell
docker exec -it postgres psql -U flink_user -d commodity_analytics
```
Then run:
```sql
SELECT ticker, event_timestamp, close_price, sma_20 FROM gold_analytics ORDER BY event_timestamp DESC LIMIT 10;
```

## Stop Everything
```powershell
docker compose down
```
