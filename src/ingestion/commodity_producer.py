"""
Commodity Price Producer
========================
Streams real-time commodity prices from Yahoo Finance into Kafka.
Works with ANY commodity defined in config.py.

Usage:
    python commodity_producer.py --ticker GC=F     # Gold
    python commodity_producer.py --ticker SI=F     # Silver
    python commodity_producer.py --ticker CL=F     # Crude Oil
    python commodity_producer.py --ticker DX-Y.NYB # US Dollar Index

Architecture:
    [Yahoo Finance API] -> [This Script] -> [Kafka: {commodity}_prices topic]

Why One Generic Script?
    DRY Principle (Don't Repeat Yourself).
    Instead of 4 identical files with different tickers hardcoded,
    we have ONE script that accepts the ticker as an argument.
    Adding a 5th commodity = one line in config.py, zero code changes here.
"""

import json
import sys
import time
import argparse
from datetime import datetime
from confluent_kafka import Producer
import yfinance as yf

from config import KAFKA_BROKER, COMMODITIES, POLL_INTERVAL


# ============================================================================
# DELIVERY CALLBACK
# ============================================================================
def delivery_callback(err, msg):
    """Called once for each message to confirm delivery."""
    if err is not None:
        print(f"ERROR: Delivery failed: {err}")


# ============================================================================
# PRICE FETCHER
# ============================================================================
def fetch_price(ticker: str) -> dict:
    """
    Fetch current price for any commodity from Yahoo Finance.

    Uses two methods (with fallback):
        1. fast_info  -> quickest, but sometimes returns None
        2. history()  -> slower but more reliable

    Args:
        ticker: Yahoo Finance ticker symbol (e.g., 'GC=F')

    Returns:
        dict with price data, or None if the API call fails.
    """
    try:
        t = yf.Ticker(ticker)
        
        # Initialize defaults
        price = None
        open_price = 0.0
        high_price = 0.0
        low_price = 0.0
        volume = 0
        previous_close = None

        # Method 1: Try fast_info first
        try:
            info = t.fast_info
            price = info.get("lastPrice", None) or info.get("last_price", None)
            previous_close = info.get("previousClose", None) or info.get("previous_close", None)
            open_price = float(info.get("open", 0) or 0)
            high_price = float(info.get("dayHigh", 0) or info.get("day_high", 0) or 0)
            low_price = float(info.get("dayLow", 0) or info.get("day_low", 0) or 0)
            volume = int(info.get("lastVolume", 0) or info.get("last_volume", 0) or 0)
        except Exception:
            # fast_info threw an error (e.g., KeyError: 'chart' for DX-Y.NYB)
            price = None

        # Method 2: Fallback to history
        if price is None:
            try:
                # Get daily history to get the previous close
                daily_hist = t.history(period="5d", interval="1d")
                if not daily_hist.empty:
                    if len(daily_hist) >= 2:
                        previous_close = float(daily_hist["Close"].iloc[-2])
                    
                # Get 1-minute history for current prices
                hist = t.history(period="5d", interval="1m")
                if not hist.empty:
                    last_row = hist.iloc[-1]
                    price = float(last_row["Close"])
                    open_price = float(last_row["Open"])
                    high_price = float(last_row["High"])
                    low_price = float(last_row["Low"])
                    volume = int(last_row["Volume"])
            except Exception:
                price = None

        # Method 3: Final fallback to t.info (API call)
        if price is None:
            full_info = t.info
            price = full_info.get("regularMarketPrice", None)
            if price is None:
                return None
            previous_close = full_info.get("regularMarketPreviousClose", 0)
            open_price = float(full_info.get("regularMarketOpen", 0))
            high_price = float(full_info.get("regularMarketDayHigh", 0))
            low_price = float(full_info.get("regularMarketDayLow", 0))
            volume = int(full_info.get("regularMarketVolume", 0))

        change_pct = 0.0
        if previous_close and previous_close > 0:
            change_pct = round(((price - previous_close) / previous_close) * 100, 4)

        return {
            "ticker": ticker,
            "close": round(float(price), 2),
            "open": round(float(open_price), 2),
            "high": round(float(high_price), 2),
            "low": round(float(low_price), 2),
            "volume": int(volume),
            "previous_close": round(float(previous_close or 0), 2),
            "change_pct": change_pct,
            "timestamp": datetime.now().isoformat(),
            "source": "live",
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"ERROR fetching price for {ticker}: {e}")
        return None


# ============================================================================
# ARGUMENT PARSER
# ============================================================================
def parse_args():
    """
    Parse command-line arguments.

    argparse is the standard Python library for handling CLI arguments.
    It automatically generates --help output and validates inputs.
    """
    parser = argparse.ArgumentParser(
        description="Stream commodity prices to Kafka"
    )
    parser.add_argument(
        "--ticker",
        required=True,
        choices=list(COMMODITIES.keys()),
        help="Yahoo Finance ticker symbol (e.g., GC=F)"
    )
    return parser.parse_args()


# ============================================================================
# MAIN LOOP
# ============================================================================
def main():
    args = parse_args()

    ticker = args.ticker
    commodity = COMMODITIES[ticker]
    topic = commodity["topic"]
    name = commodity["name"]

    print("=" * 60)
    print(f"{name} Producer Starting...")
    print(f"Ticker:   {ticker}")
    print(f"Topic:    {topic}")
    print(f"Broker:   {KAFKA_BROKER}")
    print(f"Interval: {POLL_INTERVAL}s")
    print("=" * 60)

    producer = Producer({
        "bootstrap.servers": KAFKA_BROKER,
        "client.id": f"{ticker.lower().replace('=','').replace('.','')}-producer",
    })

    message_count = 0

    try:
        while True:
            price_data = fetch_price(ticker)

            if price_data:
                message_count += 1
                payload = json.dumps(price_data).encode("utf-8")

                producer.produce(
                    topic=topic,
                    value=payload,
                    callback=delivery_callback,
                )
                producer.poll(0)

                print(f"#{message_count} | {name}: ${price_data['close']:.2f} | "
                      f"Change: {price_data['change_pct']:+.4f}%")
            else:
                print(f"#{message_count + 1} | Skipped (no data)")

            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        print(f"\nStopping... Sent {message_count} price points.")
    finally:
        producer.flush()
        print("Producer closed.")


if __name__ == "__main__":
    main()
