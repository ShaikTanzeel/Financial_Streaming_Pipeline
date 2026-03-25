# Project Structure

## Folder Layout

```
End_to_end_project/
│
├── src/                           # All source code
│   ├── ingestion/                 # Data ingestion layer
│   │   ├── config.py              # Shared settings (broker, tickers, topics)
│   │   ├── commodity_producer.py  # Live price streamer
│   │   ├── commodity_backfill.py  # Historical data loader (2yr hourly)
│   │   └── commodity_consumer.py  # Data verification consumer
│   │
│   ├── processing/                # Stream processing layer
│   │   └── create_tables.sql      # Flink source/sink table definitions
│   │
│   └── storage/                   # Database layer
│       └── init.sql               # PostgreSQL schema initialization
│
├── docs/                          # Documentation
│   ├── learning_guide.md          # Technical concepts reference
│   └── project_structure.md       # This file
│
├── external_libs/                 # Flink connector JARs (not in git)
│   ├── flink-connector-jdbc-*.jar
│   └── postgresql-*.jar
│
├── docker-compose.yml             # Infrastructure definition
├── .env.example                   # Environment variable template
├── requirements.txt               # Python dependencies
├── startup_commands.md            # Step-by-step run guide
└── README.md                      # Project overview
```

## Naming Conventions

| Type           | Convention              | Example             |
|----------------|-------------------------|---------------------|
| Folders        | lowercase, underscores  | `data_generator`    |
| Python files   | lowercase, underscores  | `kafka_producer.py` |
| Classes        | PascalCase              | `OrderProcessor`    |
| Functions      | lowercase, underscores  | `process_order()`   |
| Constants      | UPPERCASE               | `KAFKA_BROKER_URL`  |

## Design Principles

1. **Separation of Concerns** — Each folder has one responsibility
2. **Environment Isolation** — Credentials live in `.env`, not in code
3. **Reproducibility** — Anyone can clone and run with `docker compose up -d`
4. **DRY** — One generic producer handles all commodities via config
