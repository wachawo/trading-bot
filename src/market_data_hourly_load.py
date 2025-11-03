import os
import time
import requests
import pandas as pd
import schedule
import sqlite3
from pathlib import Path
from datetime import datetime
from collections import deque
from telegram_bot import send_telegram_message
from tokens import tokens

class APIRateLimiter:
    def __init__(self, max_calls, period_seconds):
        self.max_calls = max_calls
        self.period_seconds = period_seconds
        self.call_timestamps = deque()

    def wait(self):
        """Waits if necessary to respect the rate limit."""
        current_time = time.time()
        
        # Remove timestamps older than the period
        while self.call_timestamps and self.call_timestamps[0] <= current_time - self.period_seconds:
            self.call_timestamps.popleft()
            
        if len(self.call_timestamps) >= self.max_calls:
            wait_time = self.call_timestamps[0] - (current_time - self.period_seconds)
            print(f"Rate limit reached. Waiting for {wait_time:.2f} seconds...")
            if wait_time > 0:
                time.sleep(wait_time)
        
        self.call_timestamps.append(time.time())

class MarketDataHourlyLoad:
    """
    A self-contained, scheduled process to monitor cryptocurrency markets for oversold conditions.

    This class serves as the main engine of the application. It runs on an hourly schedule
    to perform a complete data refresh, calculate the Relative Strength Index (RSI) for a
    list of predefined tokens, and send alerts via Telegram if a token is identified as
    oversold (RSI < 30).

    Workflow per hourly run:
    1.  `update_historical_data()`: Deletes all existing price data from the SQLite
        database and repopulates it with the last 59 days of historical daily prices
        from the CoinGecko API. This ensures the RSI is always calculated against a
        fresh, rolling dataset.
    2.  `get_all_current_prices()`: Fetches the current USD price for all monitored
        tokens in a single, efficient, batched API call.
    3.  `run_market_check()`: Orchestrates the process. For each token, it retrieves
        the historical data from the database, appends the current price, and then
        calculates the RSI.
    4.  Alerting: If the calculated RSI is below 30, it formats and sends a
        notification message through the `send_telegram_message` function.

    Rate Limiting:
    - The class utilizes an `APIRateLimiter` instance to ensure that all calls to the
      CoinGecko API adhere to a strict limit (e.g., 25 calls per minute), preventing
      the application's IP from being temporarily blocked.
    """
    def __init__(self):
        """Initializes the market data load process."""
        print("Initializing the market data load process...")
        self.tokens_to_watch = tokens
        self.db_file = Path(__file__).parent.parent / 'data' / 'market_data.db'
        self.rate_limiter = APIRateLimiter(max_calls=25, period_seconds=60)
        self.load_dotenv()
        self.init_db()

    @staticmethod
    def load_dotenv():
        """Loads environment variables from .env file."""
        from dotenv import load_dotenv
        env_path = Path(__file__).parent.parent / '.env'
        load_dotenv(dotenv_path=env_path)

    def init_db(self):
        """Initializes the database."""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS prices (
                        token_id TEXT, token_name TEXT, token_symbol TEXT,
                        timestamp INTEGER, datetime_utc TEXT, price REAL,
                        PRIMARY KEY (token_id, timestamp)
                    )
                ''')
                conn.commit()
            print("Database initialized successfully.")
        except sqlite3.Error as e:
            print(f"Database error: {e}")

    def get_last_timestamp(self, token_id):
        """Gets the last timestamp for a token from the database."""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT MAX(timestamp) FROM prices WHERE token_id = ?", (token_id,))
                result = cursor.fetchone()[0]
                return result if result else 0
        except sqlite3.Error as e:
            print(f"Database error fetching last timestamp for {token_id}: {e}")
            return 0

    def update_historical_data(self):
        """Fetches and inserts new historical data since the last update."""
        print("--- [Hourly Job] Starting incremental refresh of historical data ---")
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                api_key = os.getenv("COINGECKO_API_KEY_ACCOUNT")
                if not api_key:
                    raise ValueError("COINGECKO API key not found.")
                headers = {"x-cg-demo-api-key": api_key}

                for token_id, token_info in self.tokens_to_watch.items():
                    last_timestamp = self.get_last_timestamp(token_id)
                    
                    # Calculate days since last update
                    if last_timestamp > 0:
                        days_to_fetch = (datetime.utcnow() - datetime.utcfromtimestamp(last_timestamp)).days
                        if days_to_fetch <= 0:
                            print(f"Data for {token_id} is already up to date.")
                            continue
                    else:
                        days_to_fetch = 59  # Initial load

                    self.rate_limiter.wait()
                    print(f"Fetching {days_to_fetch} day(s) of historical data for {token_id}...")
                    url = f"https://api.coingecko.com/api/v3/coins/{token_id}/market_chart"
                    params = {"vs_currency": "usd", "days": str(days_to_fetch), "interval": "daily"}
                    
                    response = requests.get(url, headers=headers, params=params)
                    if response.status_code == 200:
                        prices = response.json().get("prices", [])
                        
                        # Filter out the last known price to avoid duplicates
                        historical_prices = [p for p in prices if int(p[0] / 1000) > last_timestamp]
                        
                        prices_to_insert = [
                            (token_id, token_info['name'], token_info['symbol'], int(p[0] / 1000), 
                             datetime.utcfromtimestamp(int(p[0] / 1000)).strftime('%Y-%m-%d %H:%M:%S'), p[1])
                            for p in historical_prices
                        ]
                        if prices_to_insert:
                            cursor.executemany("INSERT OR IGNORE INTO prices VALUES (?, ?, ?, ?, ?, ?)", prices_to_insert)
                            print(f"Inserted {len(prices_to_insert)} new historical price points for {token_id}.")
                    else:
                        print(f"Failed to fetch API data for {token_id}. Status: {response.status_code}")
                conn.commit()
            print("--- [Hourly Job] Historical data refresh complete ---")
        except Exception as e:
            print(f"An error occurred during historical data update: {e}")

    def get_all_current_prices(self):
        """Fetches the current price for all watched tokens in a single batch."""
        print("Fetching current prices for all tokens...")
        try:
            token_ids = ",".join(self.tokens_to_watch.keys())
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {"ids": token_ids, "vs_currencies": "usd"}
            api_key = os.getenv("COINGECKO_API_KEY_ACCOUNT")
            headers = {"x-cg-demo-api-key": api_key}
            
            self.rate_limiter.wait()
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API error while fetching current prices: {e}")
            return {}

    def get_historical_prices_from_db(self, token_id):
        """Fetches historical prices from the database."""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT timestamp, price FROM prices WHERE token_id = ? ORDER BY timestamp ASC", (token_id,))
                prices = cursor.fetchall()
            return [[p[0] * 1000, p[1]] for p in prices]
        except sqlite3.Error as e:
            print(f"Database error fetching historical prices: {e}")
            return []

    @staticmethod
    def calculate_rsi(prices, period=14):
        """Calculates the RSI from a list of price data."""
        if len(prices) < period + 1:
            return None
        
        df = pd.DataFrame(prices, columns=["timestamp", "price"])
        delta = df['price'].diff()
        gain = (delta.where(delta > 0, 0)).ewm(alpha=1/period, adjust=False).mean()
        loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/period, adjust=False).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return round(rsi.iloc[-1], 2)

    def run_market_check(self):
        """Main job to refresh data, calculate RSI, and send alerts."""
        print("\n--- [Scheduled Job] Starting Market Check ---")
        self.update_historical_data()
        
        current_prices = self.get_all_current_prices()
        if not current_prices:
            print("Could not fetch current prices. Skipping market check.")
            return

        for token_id, token_info in self.tokens_to_watch.items():
            symbol = token_info['symbol']
            print(f"Processing token: {symbol}")

            historical_prices = self.get_historical_prices_from_db(token_id)
            if not historical_prices:
                print(f"No historical data for {symbol}. Skipping.")
                continue

            current_price_data = current_prices.get(token_id)
            if not current_price_data or 'usd' not in current_price_data:
                print(f"No current price for {symbol}. Skipping.")
                continue
            
            current_price = [[int(time.time() * 1000), current_price_data['usd']]]
            all_prices = historical_prices + current_price
            
            rsi_value = self.calculate_rsi(all_prices)
            if rsi_value is not None:
                print(f"RSI for {symbol}: {rsi_value}")
                if rsi_value < 30:
                    print(f"ALERT: {symbol} is oversold with RSI: {rsi_value}")
                    message = f"🚨 *Oversold Alert!* 🚨\n\n**Token:** {symbol}\n**RSI:** {rsi_value:.2f}"
                    send_telegram_message(message)
            else:
                print(f"Could not calculate RSI for {symbol}.")

        print("--- [Scheduled Job] Market Check Complete ---")

    def start(self):
        """Starts the scheduled job."""
        print("Process is now running. Press Ctrl+C to exit.")
        schedule.every().hour.do(self.run_market_check)
        self.run_market_check()
        while True:
            schedule.run_pending()
            time.sleep(1)

if __name__ == "__main__":
    market_loader = MarketDataHourlyLoad()
    market_loader.start()
