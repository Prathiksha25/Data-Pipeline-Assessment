#!/usr/bin/env python3

import os
import sys
import time
import logging
from datetime import datetime
import requests
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

# --- Logging setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# --- Config from env ---
POSTGRES_USER = os.environ.get("POSTGRES_USER", "airflow")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "airflow_pass_here")
POSTGRES_DB = os.environ.get("POSTGRES_DB", "stocks_db")
POSTGRES_PORT = int(os.environ.get("POSTGRES_PORT", 5432))
POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "postgres")  # docker service name
STOCK_API_KEY = os.environ.get("STOCK_API_KEY", "")
STOCK_API_URL = os.environ.get("STOCK_API_URL", "https://www.alphavantage.co/query")
STOCK_SYMBOL = os.environ.get("STOCK_SYMBOL", "IBM")
STOCKS_TABLE_NAME = os.environ.get("STOCKS_TABLE_NAME", "stock_prices")
# How many recent points to insert (1 is fine for this assignment)
NUM_POINTS = int(os.environ.get("STOCK_FETCH_POINTS", 1))


def fetch_from_alpha_vantage(symbol: str, api_key: str, url: str, num_points: int = 1):
    """
    Fetch intraday or daily price (fallback to TIME_SERIES_DAILY).
    Returns a pandas DataFrame with columns: symbol, timestamp, open, high, low, close, volume
    """
    logger.info("Fetching data from Alpha Vantage for %s", symbol)
    # Try intraday (1min) first (free tier may be limited) then daily
    params_intraday = {
        "function": "TIME_SERIES_INTRADAY",
        "symbol": symbol,
        "interval": "60min",
        "apikey": api_key,
        "outputsize": "compact"
    }
    try:
        r = requests.get(url, params=params_intraday, timeout=30)
        r.raise_for_status()
        data = r.json()
        if "Time Series (60min)" in data:
            series = data["Time Series (60min)"]
        elif "Note" in data:
            # rate limit note - fallback to daily
            logger.warning("Alpha Vantage rate limit or note: %s", data.get("Note"))
            raise ValueError("rate_limited")
        else:
            # fallback to daily
            raise ValueError("intraday_unavailable")
    except Exception as e:
        logger.info("Intraday unavailable or failed (%s). Falling back to daily.", e)
        params_daily = {
            "function": "TIME_SERIES_DAILY_ADJUSTED",
            "symbol": symbol,
            "apikey": api_key,
            "outputsize": "compact"
        }
        r = requests.get(url, params=params_daily, timeout=30)
        r.raise_for_status()
        data = r.json()
        if "Time Series (Daily)" not in data:
            raise RuntimeError(f"Unexpected response from Alpha Vantage: {data}")
        series = data["Time Series (Daily)"]

    # Convert to DataFrame
    rows = []
    for ts, values in series.items():
        try:
            ts_dt = datetime.fromisoformat(ts)
        except Exception:
            ts_dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S") if " " in ts else datetime.strptime(ts, "%Y-%m-%d")
        row = {
            "symbol": symbol,
            "timestamp": ts_dt,
            "open": float(values.get("1. open", values.get("1. open", 0))),
            "high": float(values.get("2. high", values.get("2. high", 0))),
            "low": float(values.get("3. low", values.get("3. low", 0))),
            "close": float(values.get("4. close", values.get("4. close", 0))),
            "volume": int(float(values.get("5. volume", values.get("6. volume", 0))))
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    df.sort_values("timestamp", ascending=False, inplace=True)
    return df.head(num_points)


def generate_sample_data(symbol: str, num_points: int = 1):
    
    logger.info("Generating sample data for %s (no API key provided)", symbol)
    now = datetime.utcnow()
    rows = []
    for i in range(num_points):
        ts = now
        close = 100.0 + i  # simple incrementing price
        rows.append({
            "symbol": symbol,
            "timestamp": ts,
            "open": close - 0.5,
            "high": close + 0.5,
            "low": close - 1.0,
            "close": close,
            "volume": 1000 + i * 10
        })
    return pd.DataFrame(rows)


def ensure_table_and_upsert(conn, table_name: str, df: pd.DataFrame):
   
    with conn.cursor() as cur:
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            symbol TEXT NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            open DOUBLE PRECISION,
            high DOUBLE PRECISION,
            low DOUBLE PRECISION,
            close DOUBLE PRECISION,
            volume BIGINT,
            UNIQUE (symbol, timestamp)
        );
        """
        cur.execute(create_table_sql)
        conn.commit()

        # Prepare upsert using execute_values for bulk insert
        records = [
            (row.symbol, row.timestamp, row.open, row.high, row.low, row.close, int(row.volume))
            for row in df.itertuples(index=False)
        ]
        if not records:
            logger.info("No records to insert.")
            return

        insert_sql = f"""
        INSERT INTO {table_name} (symbol, timestamp, open, high, low, close, volume)
        VALUES %s
        ON CONFLICT (symbol, timestamp) DO UPDATE SET
            open = EXCLUDED.open,
            high = EXCLUDED.high,
            low = EXCLUDED.low,
            close = EXCLUDED.close,
            volume = EXCLUDED.volume;
        """
        execute_values(cur, insert_sql, records)
        conn.commit()
        logger.info("Upserted %d rows into %s", len(records), table_name)


def main():
    # Determine fetch method
    if STOCK_API_KEY:
        try:
            df = fetch_from_alpha_vantage(STOCK_SYMBOL, STOCK_API_KEY, STOCK_API_URL, NUM_POINTS)
        except Exception as e:
            logger.exception("Failed to fetch from Alpha Vantage, falling back to sample data: %s", e)
            df = generate_sample_data(STOCK_SYMBOL, NUM_POINTS)
    else:
        df = generate_sample_data(STOCK_SYMBOL, NUM_POINTS)

    # Connect to Postgres
    conn_str = f"host={POSTGRES_HOST} port={POSTGRES_PORT} dbname={POSTGRES_DB} user={POSTGRES_USER} password={POSTGRES_PASSWORD}"
    logger.info("Connecting to postgres with host=%s db=%s user=%s", POSTGRES_HOST, POSTGRES_DB, POSTGRES_USER)
    try:
        conn = psycopg2.connect(conn_str)
    except Exception as e:
        logger.exception("Unable to connect to Postgres: %s", e)
        raise

    try:
        ensure_table_and_upsert(conn, STOCKS_TABLE_NAME, df)
    finally:
        conn.close()
        logger.info("Postgres connection closed")

    logger.info("Script finished successfully.")


if __name__ == "__main__":
    main()
