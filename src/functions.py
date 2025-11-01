import os
import requests
import pandas as pd
import time

def call_coingecko_api(tokens): 
    """
    Fetches historical market data from the CoinGecko API for a dictionary of tokens.

    This function iterates through a dictionary of cryptocurrency tokens, calling the
    CoinGecko API to retrieve the last 60 days of daily market chart data for each.
    It handles API errors gracefully, printing a message for any failed requests
    without stopping the process.

    Args:
        tokens_dict (dict): A dictionary where keys are the CoinGecko API IDs (e.g., "bitcoin")
                          and values are another dictionary containing the token's 'name'
                          and 'symbol'.
        key (str): Your CoinGecko API key for authenticating the requests.

    Returns:
        dict: A dictionary containing the successfully fetched market data. Each key is the
              token's API ID, and the value contains the token's name, symbol, and the
              market data returned by the API. Returns an empty dictionary if no data
              could be fetched.
    """

    # Initialize the market data dictionary
    market_data = {}

    # Loop through the keys (the api_id) of the dictionary
    for token_id in tokens.keys():

        token_info = tokens[token_id]
        token_name = token_info['name']
        token_symbol = token_info['symbol']

        # API Key config
        api_key = os.getenv("COINGECKO_API_KEY_ACCOUNT1")
        if not api_key:
            raise ValueError("COINGECKO_API_KEY_ACCOUNT1 not found in .env file.")

        # API variables
        url = f"https://api.coingecko.com/api/v3/coins/{token_id}/market_chart"
        api_key = os.getenv("COINGECKO_API_KEY_ACCOUNT1")
        headers = { "x-cg-demo-api-key": api_key }
        parameters = { "vs_currency": "usd", "days": "60", "interval": "daily" }    
        
        time.sleep(2) # Delay to respect API rate limits (30 calls per minute)
        response = requests.get(url, headers=headers, params=parameters)
        
        if response.status_code == 200:
            market_data[token_id] = {
                "name": token_name,
                "symbol": token_symbol,
                "market_data": response.json()
            }
            print(f"Successfully fetched market data for {token_name} ({token_symbol})")
        else:
            print(f"Response status code: {response.status_code}")

    return market_data

def calculate_rsi(market_data, period=14):
    """
    Calculates the RSI for each token using a standard EMA-based method
    to align with platforms like TradingView.

    Args:
        market_data (dict): The output from the call_coingecko_api function.
        period (int): The time period for the RSI calculation (default is 14).

    Returns:
        dict: A dictionary with token symbols as keys and their latest RSI as values,
              rounded to two decimal places.
    """

    if not market_data:
        print("No market data found.")
        return None
    
    rsi_results = {}

    for token_id, token_data in market_data.items():
        #Extract the price data for the current token
        prices = token_data.get("market_data", {}).get("prices", [])

        if prices:
            # Create a pandas DataFrame from the price data
            df = pd.DataFrame(prices, columns=["timestamp", "price"])

            # Convert the price column to numeric
            df['price'] = pd.to_numeric(df['price'])

            # Calculate price changes
            delta = df['price'].diff()

            # Separate gains and losses
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

            # Use Exponential Moving Average (EMA) for smoothing, which is the standard for RSI.
            # The 'com' (center of mass) parameter is set to period - 1 to match Wilder's smoothing.
            avg_gain = gain.ewm(com=period - 1, min_periods=period, adjust=False).mean()
            avg_loss = loss.ewm(com=period - 1, min_periods=period, adjust=False).mean()

            # Calculate the Relative Strength (RS) and the RSI
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

            # Get the last RSI value and round it to two decimal places
            last_rsi = rsi.iloc[-1]

            if pd.notna(last_rsi):
                rsi_results[token_data['symbol']] = {'rsi': round(last_rsi, 2)}
            else:
                rsi_results[token_data['symbol']] = {'rsi': None}
        else:
            rsi_results[token_data['symbol']] = {'rsi': None}
            
    return rsi_results
