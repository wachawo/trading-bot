import os
from dotenv import load_dotenv
from apexomni.constants import APEX_OMNI_HTTP_MAIN, NETWORKID_OMNI_MAIN_ARB
from apexomni.http_private_v3 import HttpPrivate_v3

load_dotenv()

# --- IMPORTANT ---
# Make sure you have a .env file with your API credentials
API_KEY = os.environ.get("APEX_API_KEY")
API_SECRET = os.environ.get("APEX_API_SECRET")
API_PASSPHRASE = os.environ.get("APEX_PASSPHRASE")

if not all([API_KEY, API_SECRET, API_PASSPHRASE]):
    print("Please make sure you have a .env file with your APEX_API_KEY, APEX_API_SECRET, and APEX_PASSPHRASE.")
    exit()

# Initialize the private client
client = HttpPrivate_v3(
    APEX_OMNI_HTTP_MAIN,
    network_id=NETWORKID_OMNI_MAIN_ARB,
    api_key_credentials={
        'key': API_KEY,
        'secret': API_SECRET,
        'passphrase': API_PASSPHRASE
    }
)

# Fetch and print account data
try:
    print("Fetching initial configurations...")
    configs = client.configs_v3()
    print("Configurations fetched successfully.")

    print("\nFetching user account data...")
    account_data = client.get_account_v3()
    print("\n--- User Account Data ---")
    print(account_data)
    print("-------------------------\n")

except Exception as e:
    print(f"An error occurred: {e}")
