"""
Commodity Backfill Script
==========================
Fetches 2 years of historical data for any commodity and loads it into Kafka.

Usage:
    python commodity_backfill.py --ticker GC=F       # Gold
    python commodity_backfill.py --ticker SI=F       # Silver
    python commodity_backfill.py --ticker CL=F       # Crude Oil
    python commodity_backfill.py --ticker DX-Y.NYB   # US Dollar Index
    python commodity_backfill.py --all                # All 4 at once

Purpose:
    Runs ONCE per commodity to populate Kafka with historical data.
    After this, commodity_producer.py streams live data on top.

Architecture:
    [Yahoo Finance: 2yr history] -> [This Script] -> [Kafka: {commodity}_prices]
"""

import json
import time
import argparse
from confluent_kafka import Producer
import yfinance as yf

from config import KAFKA_BROKER, COMMODITIES


# ============================================================================
# DELIVERY CALLBACK
# ============================================================================
def delivery_callback(err, msg):
    """Called once for each message to confirm delivery."""
    if err is not None:
        print(f"ERROR: Delivery failed: {err}")


# ============================================================================
# FETCH HISTORICAL DATA
# ============================================================================
def fetch_historical_data(ticker: str) -> list:
    """
    Fetch 2 years of hourly data for a given commodity.

    Args:
        ticker: Yahoo Finance ticker symbol

    Returns:
        list of dicts, each dict is one hourly candle (OHLCV)
    """
    name = COMMODITIES[ticker]["name"]
    print(f"Fetching 2 years of hourly data for {name} ({ticker})...")

    t = yf.Ticker(ticker)
    history = t.history(period="2y", interval="1h")

    if history.empty:
        print(f"ERROR: No historical data returned for {ticker}!")
        return []

    print(f"Received {len(history)} rows from Yahoo Finance.")

    records = []
    for index, row in history.iterrows():
        record = {
            "ticker": ticker,
            "timestamp": index.isoformat(),
            "open": round(float(row["Open"]), 2),
            "high": round(float(row["High"]), 2),
            "low": round(float(row["Low"]), 2),
            "close": round(float(row["Close"]), 2),
            "volume": int(row["Volume"]),
            "source": "backfill",
        }
        records.append(record)

    return records


# ============================================================================
# SEND TO KAFKA
# ============================================================================
def send_to_kafka(ticker: str, records: list):
    """Send historical records to the appropriate Kafka topic."""
    topic = COMMODITIES[ticker]["topic"]
    name = COMMODITIES[ticker]["name"]

    producer = Producer({
        "bootstrap.servers": KAFKA_BROKER,
        "client.id": f"{ticker.lower().replace('=','').replace('.','')}-backfill",
    })

    print(f"Sending {len(records)} {name} records to '{topic}'...")
    sent = 0

    for record in records:
        payload = json.dumps(record).encode("utf-8")

        producer.produce(
            topic=topic,
            value=payload,
            callback=delivery_callback,
        )

        sent += 1
        if sent % 500 == 0:
            producer.poll(0)
            print(f"  Sent {sent}/{len(records)} records...")

    producer.flush()
    print(f"Done! Sent {sent} records to '{topic}'.")
    return sent


# ============================================================================
# ARGUMENT PARSER
# ============================================================================
def parse_args():
    parser = argparse.ArgumentParser(
        description="Backfill historical commodity data into Kafka"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--ticker",
        choices=list(COMMODITIES.keys()),
        help="Backfill a single commodity"
    )
    group.add_argument(
        "--all",
        action="store_true",
        help="Backfill ALL commodities (with delays to avoid rate limiting)"
    )
    return parser.parse_args()


# ============================================================================
# MAIN
# ============================================================================
def main():
    args = parse_args()

    # Determine which tickers to backfill
    if args.all:
        tickers = list(COMMODITIES.keys())
    else:
        tickers = [args.ticker]

    print("=" * 60)
    print("Commodity Backfill Starting...")
    print(f"Broker: {KAFKA_BROKER}")
    print(f"Commodities: {', '.join(tickers)}")
    print("=" * 60)

    total_sent = 0

    for i, ticker in enumerate(tickers):
        name = COMMODITIES[ticker]["name"]
        print(f"\n--- [{i+1}/{len(tickers)}] {name} ({ticker}) ---")

        # Fetch historical data
        records = fetch_historical_data(ticker)
        if not records:
            print(f"Skipping {ticker} (no data).")
            continue

        # Send to Kafka
        sent = send_to_kafka(ticker, records)
        total_sent += sent

        # Wait between commodities to avoid rate limiting
        if i < len(tickers) - 1:
            print("Waiting 5 seconds before next commodity (rate limit)...")
            time.sleep(5)

    print("\n" + "=" * 60)
    print(f"Backfill Complete! Total records sent: {total_sent}")
    print("=" * 60)


if __name__ == "__main__":
    main()
