import os
import time
import requests
import pandas as pd
import schedule
import sqlite3
from pathlib import Path
from datetime import datetime
from telegram_bot import send_telegram_message
from tokens import tokens

class MarketDataHourlyLoad:
    def __init__(self):
        """Initializes the hourly market data load process."""
        print("Initializing the market data load process...")
        self.tokens_to_watch = tokens
        self.db_file = Path(__file__).parent.parent / 'market_data.db'
        self.load_dotenv()
        self.init_db() # Ensure the database is ready on startup

    @staticmethod
    def load_dotenv():
        """Loads environment variables from .env file."""
        from dotenv import load_dotenv
        env_path = Path(__file__).parent.parent / '.env'
        load_dotenv(dotenv_path=env_path)

    def init_db(self):
        """Initializes the database and creates the prices table if it doesn't exist."""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS prices (
                    token_id TEXT,
                    token_name TEXT,
                    token_symbol TEXT,
                    timestamp INTEGER,
                    datetime_utc TEXT,
                    price REAL,
                    PRIMARY KEY (token_id, timestamp)
                )
            ''')
            conn.commit()
            conn.close()
            print("Database initialized successfully.")
        except sqlite3.Error as e:
            print(f"Database error: {e}")

    def update_historical_data(self):
        """
        Clears and repopulates the database with the last 59 days of daily historical data.
        """
        print("--- [Hourly Job] Starting full refresh of historical data ---")
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM prices")
            print("Cleared old data from the prices table.")

            api_key = os.getenv("COINGECKO_API_KEY_ACCOUNT1")
            if not api_key:
                raise ValueError("COINGECKO_API_KEY_ACCOUNT1 not found in .env file.")
            headers = { "x-cg-demo-api-key": api_key }

            for token_id, token_info in self.tokens_to_watch.items():
                print(f"Fetching last 59 days of daily data for {token_id}...")
                url = f"https://api.coingecko.com/api/v3/coins/{token_id}/market_chart"
                params = { "vs_currency": "usd", "days": "59", "interval": "daily" }
                
                time.sleep(1) # Respect API rate limits
                response = requests.get(url, headers=headers, params=params)

                if response.status_code == 200:
                    data = response.json()
                    prices = data.get("prices", [])
                    today_utc = datetime.utcnow().date()

                    if prices:
                        historical_prices = [p for p in prices if datetime.utcfromtimestamp(p[0] / 1000).date() < today_utc]
                        
                        prices_to_insert = [
                            (token_id, token_info['name'], token_info['symbol'], int(p[0] / 1000), datetime.utcfromtimestamp(int(p[0] / 1000)).strftime('%Y-%m-%d %H:%M:%S'), p[1])
                            for p in historical_prices
                        ]

                        if prices_to_insert:
                            cursor.executemany(
                                "INSERT OR IGNORE INTO prices (token_id, token_name, token_symbol, timestamp, datetime_utc, price) VALUES (?, ?, ?, ?, ?, ?)",
                                prices_to_insert
                            )
                            print(f"Successfully inserted {len(prices_to_insert)} historical price points for {token_id}.")
                else:
                    print(f"Failed to fetch API data for {token_id}. Status: {response.status_code}")
            
            conn.commit()
            conn.close()
            print("--- [Hourly Job] Historical data refresh complete ---")

        except sqlite3.Error as e:
            print(f"A database error occurred: {e}")
        except Exception as e:
            print(f"An unexpected error occurred during historical data update: {e}")

    def get_historical_prices_from_db(self, token_id):
        """Fetches historical prices from the database."""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute("SELECT timestamp, price FROM prices WHERE token_id = ? ORDER BY timestamp ASC", (token_id,))
            prices = cursor.fetchall()
            conn.close()
            return [[p[0] * 1000, p[1]] for p in prices]
        except sqlite3.Error as e:
            print(f"Database error while fetching historical prices: {e}")
            return []

    def get_current_price(self, token_id):
        """Fetches the current price for a single token."""
        try:
            url = f"https://api.coingecko.com/api/v3/simple/price"
            params = {"ids": token_id, "vs_currencies": "usd"}
            api_key = os.getenv("COINGECKO_API_KEY_ACCOUNT1")
            headers = {"x-cg-demo-api-key": api_key}
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            price = data.get(token_id, {}).get("usd")
            if price:
                timestamp = int(datetime.now().timestamp() * 1000)
                return [[timestamp, price]]
            return []
        except requests.exceptions.RequestException as e:
            print(f"API error while fetching current price for {token_id}: {e}")
            return []

    @staticmethod
    def calculate_rsi(prices, period=14):
        """Calculates the RSI from a list of price data."""
        if len(prices) < period + 1:
            print(f"Not enough data to calculate RSI. Need {period + 1}, have {len(prices)}.")
            return None
        
        df = pd.DataFrame(prices, columns=["timestamp", "price"])
        df['price'] = pd.to_numeric(df['price'])
        delta = df['price'].diff()
        
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.rolling(window=period, min_periods=1).mean().iloc[-1]
        avg_loss = loss.rolling(window=period, min_periods=1).mean().iloc[-1]

        # Use Wilder's smoothing for subsequent calculations
        for i in range(period, len(df)):
            avg_gain = (avg_gain * (period - 1) + gain.iloc[i]) / period
            avg_loss = (avg_loss * (period - 1) + loss.iloc[i]) / period
        
        if avg_loss == 0:
            return 100 # Prevent division by zero
            
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return round(rsi, 2)

    def run_market_check(self):
        """Main job to refresh data, calculate RSI, and send alerts."""
        print("\n--- [Scheduled Job] Starting Market Check ---")
        
        # Every time it runs, first refresh the entire historical dataset
        self.update_historical_data()

        for token_id, token_info in self.tokens_to_watch.items():
            symbol = token_info['symbol']
            print(f"Processing token: {symbol}")

            historical_prices = self.get_historical_prices_from_db(token_id)
            if not historical_prices:
                print(f"No historical data found for {symbol} after refresh. Skipping.")
                continue

            current_price = self.get_current_price(token_id)
            if not current_price:
                print(f"Could not fetch current price for {symbol}. Skipping.")
                continue
            
            all_prices = historical_prices + current_price
            print(f"Combined data points for {symbol}: {len(all_prices)}")

            rsi_value = self.calculate_rsi(all_prices)
            if rsi_value is not None:
                print(f"RSI for {symbol}: {rsi_value}")
                
                oversold_num = 30
                if rsi_value < oversold_num:
                    print(f"ALERT: {symbol} is oversold with RSI: {rsi_value}")
                    message = (
                        f"🚨 *Oversold Alert!* 🚨\n\n"
                        f"**Token:** {symbol}\n"
                        f"**RSI:** {rsi_value:.2f}"
                    )
                    send_telegram_message(message)
            else:
                print(f"Could not calculate RSI for {symbol}.")

        print("--- [Scheduled Job] Market Check Complete ---")

    def start(self):
        """Starts the scheduled job."""
        print("Process is now running. Press Ctrl+C to exit.")
        schedule.every().hour.do(self.run_market_check)
        self.run_market_check() # Run once immediately
        while True:
            schedule.run_pending()
            time.sleep(1)

if __name__ == "__main__":
    market_loader = MarketDataHourlyLoad()
    market_loader.start()
