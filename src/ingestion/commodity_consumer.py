"""
Commodity Price Consumer
========================
Reads price data from Kafka for any commodity and displays it.

Usage:
    python commodity_consumer.py --ticker GC=F       # Watch Gold
    python commodity_consumer.py --ticker SI=F       # Watch Silver
    python commodity_consumer.py --all                # Watch ALL commodities

Architecture:
    [Kafka: {commodity}_prices topic] -> [This Script] -> [Terminal Display]
"""

import json
import argparse
from confluent_kafka import Consumer, KafkaError

from config import KAFKA_BROKER, COMMODITIES


# ============================================================================
# MESSAGE PROCESSOR
# ============================================================================
def process_message(data: dict):
    """Format and print commodity price data."""
    ticker = data.get("ticker", "???")
    name = COMMODITIES.get(ticker, {}).get("name", ticker)
    source = data.get("source", "live").upper()

    # Handle both backfill format (close) and live format (price)
    price = data.get("close") or data.get("price", 0)

    print(f"[{source}] {name}: ${price:.2f} | {data.get('timestamp', 'N/A')}")


# ============================================================================
# ARGUMENT PARSER
# ============================================================================
def parse_args():
    parser = argparse.ArgumentParser(
        description="Consume commodity prices from Kafka"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--ticker",
        choices=list(COMMODITIES.keys()),
        help="Watch a single commodity"
    )
    group.add_argument(
        "--all",
        action="store_true",
        help="Watch ALL commodities"
    )
    return parser.parse_args()


# ============================================================================
# MAIN LOOP
# ============================================================================
def main():
    args = parse_args()

    # Determine which topics to subscribe to
    if args.all:
        topics = [c["topic"] for c in COMMODITIES.values()]
        label = "All Commodities"
    else:
        topics = [COMMODITIES[args.ticker]["topic"]]
        label = COMMODITIES[args.ticker]["name"]

    print("=" * 60)
    print(f"Commodity Consumer: {label}")
    print(f"Topics: {', '.join(topics)}")
    print("=" * 60)

    consumer = Consumer({
        "bootstrap.servers": KAFKA_BROKER,
        "group.id": "commodity-monitor-v1",
        "auto.offset.reset": "earliest",
        "enable.auto.commit": True,
    })

    consumer.subscribe(topics)
    print("Waiting for data... (Ctrl+C to stop)")

    message_count = 0

    try:
        while True:
            msg = consumer.poll(timeout=1.0)

            if msg is None:
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    print(f"Consumer Error: {msg.error()}")
                    break

            data = json.loads(msg.value().decode("utf-8"))
            message_count += 1
            process_message(data)

    except KeyboardInterrupt:
        print(f"\nStopping... Read {message_count} messages.")
    finally:
        consumer.close()


if __name__ == "__main__":
    main()
