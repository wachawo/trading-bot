#%%
import os
import sys
import requests
from dotenv import load_dotenv
from tokens import tokens
import functions
import pandas as pd

def main():
    return None

if __name__ == "__main__":

# === Environment Config # ===
    load_dotenv() 
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))


# #%%
# market_data = functions.call_coingecko_api(tokens)
# print(market_data)


# # %%
# market_data = functions.call_coingecko_api(tokens)
# rsi_values = functions.calculate_rsi(market_data)
# print(rsi_values)
# # %%
