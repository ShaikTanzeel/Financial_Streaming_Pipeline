"""
Shared Configuration
====================
Single source of truth for all ingestion settings.

Why a config file?
    Instead of hardcoding "localhost:9092" in every script,
    we define it ONCE here. If the broker address changes,
    we only update ONE file.

In production, these would come from environment variables
or a secrets manager (AWS Secrets Manager, HashiCorp Vault).
"""

import os

# Kafka connection
# os.getenv() checks for an environment variable first,
# falls back to the default value if not set.
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")

# Producer settings
POLL_INTERVAL = 10          # Seconds between API calls

# All supported commodities
# Each entry maps: ticker -> (topic_name, display_name)
# This dictionary is the SINGLE SOURCE OF TRUTH for what we track.
COMMODITIES = {
    "GC=F": {
        "topic": "gold_prices",
        "name": "Gold Futures",
    },
    "SI=F": {
        "topic": "silver_prices",
        "name": "Silver Futures",
    },
    "CL=F": {
        "topic": "oil_prices",
        "name": "Crude Oil Futures",
    },
    "DX-Y.NYB": {
        "topic": "usd_prices",
        "name": "US Dollar Index",
    },
}

# Analytics output topic (Flink will write here)
ANALYTICS_TOPIC = "commodity_analytics"
