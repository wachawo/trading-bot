#%%
from langgraph.graph import StateGraph, START, END 
import random
from typing import Dict, List, TypedDict
import requests
import time
from dotenv import load_dotenv
#%%
load_dotenv()

class AgentState(TypedDict):
    message: str
    token_historical_prices: Dict[str, List]

# %%
token_watch_list = [ 
    "bitcoin",
    "ethereum",
    "solana"
    # "optimism",
    # "render-token",
    # "polkadot",
    # "uniswap",
    # "chainlink",
    # "aave",
    # "binancecoin",
    # "pendle",
    # "tron",
    # "ripple", ## "xrp"
    # "avalanche-2",
    # "cardano",
    # "pepe",
    # "superfarm", ## "superverse",
    # "dogecoin",
    # "raydium",
    # "jito-governance-token", ## "jito",
    # "jupiter-exchange-solana",
    # "hyperliquid",
    # "sui",
    # "ethena",
    # "pump-fun",
    # "shiba-inu",
    # "arbitrum",
    # "1000bonk",
    # "based-brett",
    # "virtual-protocol",
    # "simon-s-cat",
    # "pudgy-penguins",
    # "ondo-finance",
    # "aerodrome-finance",
    # "binancecoin",
    # "kamino",
    # "beefy-finance"

######
    ## "ponke"
    ## "orca"
    ## "chill-guy"
]
# %%
def get_token_historical_price(state: AgentState) -> AgentState:
    """HTTP request to the coingecko API to get historical price data for a list of tokens, with rate limiting and retries."""
    token_historical_prices = {}
    headers = {
        "x-cg-demo-api-key": "COINGECKO_API_KEY_ACCOUNT1"    
    }        
    params = {
        "vs_currency": "usd",
        "days": "60",
        "interval": "daily"
    }
    min_interval = 2.0  # seconds (30 requests per minute)
    retries = 2
    retry_delay = 2.0  # seconds
    last_request_time = None

    for token in token_watch_list:
        if last_request_time is not None:
            elapsed = time.time() - last_request_time
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
        attempt = 0
        success = False
        while attempt <= retries:
            try:
                url = f"https://api.coingecko.com/api/v3/coins/{token}/market_chart"
                response = requests.get(url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                token_historical_prices[token] = data.get("prices", [])
                print(f"Successfully fetched data for {token}")
                success = True
                break  # success, exit retry loop
            except requests.exceptions.RequestException as e:
                print(f"Error fetching data for {token} (attempt {attempt+1}): {e}")
                if attempt < retries:
                    time.sleep(retry_delay)
                else:
                    token_historical_prices[token] = []
            attempt += 1
        last_request_time = time.time()
    state['token_historical_prices'] = token_historical_prices
    state['message'] = "Fetched historical prices for tokens."
    return state

# %%
graph = StateGraph(AgentState)

graph.add_node("get_token_historical_price", get_token_historical_price)
graph.add_edge(START, "get_token_historical_price")
graph.add_edge("get_token_historical_price", END)
agent = graph.compile()

# %%
if __name__ == "__main__":
    initial_state = AgentState(message="start", token_historical_prices={})
    final_state = agent.invoke(initial_state)
    
    print("\n--- Agent Final State ---")
    # Pretty print the result
    import json
    print(json.dumps(final_state, indent=2))
    print("-----------------------")
    # %%
