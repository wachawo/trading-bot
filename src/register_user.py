import os
import time
from dotenv import load_dotenv
from apexomni.constants import APEX_OMNI_HTTP_MAIN, NETWORKID_OMNI_MAIN_ARB, NETWORKID_MAIN
from apexomni.http_private_v3 import HttpPrivate_v3

load_dotenv()

# --- IMPORTANT ---
# Make sure you have a .env file with your ETH_PRIVATE_KEY
ETH_PRIVATE_KEY = os.environ.get("ETH_PRIVATE_KEY")

if not ETH_PRIVATE_KEY:
    print("Please make sure you have a .env file with your ETH_PRIVATE_KEY.")
    exit()

print("Initializing client with your Ethereum private key...")
client = HttpPrivate_v3(
    APEX_OMNI_HTTP_MAIN,
    network_id=NETWORKID_MAIN,
    eth_private_key=ETH_PRIVATE_KEY
)

try:
    print("Fetching initial configurations...")
    configs = client.configs_v3()
    print("Configurations fetched successfully.")

    print("\nDeriving L2 keys (zkKeys)...")
    zkKeys = client.derive_zk_key(client.default_address)
    print("zkKeys derived successfully.")
    print(f"  L2 Key: {zkKeys['l2Key']}")

    print("\nGenerating nonce...")
    nonce_res = client.generate_nonce_v3(
        refresh="false",
        l2Key=zkKeys['l2Key'],
        ethAddress=client.default_address,
        chainId=NETWORKID_OMNI_MAIN_ARB
    )
    nonce = nonce_res['data']['nonce']
    print("Nonce generated successfully.")

    print("\nRegistering user...")
    reg_res = client.register_user_v3(
        nonce=nonce,
        l2Key=zkKeys['l2Key'],
        seeds=zkKeys['seeds'],
        ethereum_address=client.default_address
    )
    print("User registration successful.")

    # --- YOUR API CREDENTIALS ---
    api_key = reg_res['data']['apiKey']
    print("\n" + "="*40)
    print("      *** YOUR API CREDENTIALS ***")
    print(f"  API Key:      {api_key['key']}")
    print(f"  API Secret:   {api_key['secret']}")
    print(f"  Passphrase:   {api_key['passphrase']}")
    print("="*40 + "\n")
    print("Please save these credentials securely. You will need them to make authenticated API calls.")
    # -----------------------------

    print("\nWaiting 10 seconds before finalizing registration...")
    time.sleep(10)

    print("Fetching account details...")
    account_res = client.get_account_v3()

    print("\nFinalizing registration by changing public key...")
    change_res = client.change_pub_key_v3(
        chainId=NETWORKID_OMNI_MAIN_ARB,
        seeds=zkKeys.get('seeds'),
        ethPrivateKey=ETH_PRIVATE_KEY,
        zkAccountId=account_res.get('spotAccount').get('zkAccountId'),
        subAccountId=account_res.get('spotAccount').get('defaultSubAccountId'),
        newPkHash=zkKeys.get('pubKeyHash'),
        nonce=account_res.get('spotAccount').get('nonce'),
        l2Key=zkKeys.get('l2Key')
    )
    print("Public key changed successfully.")
    print(change_res)

    print("\nWaiting 10 seconds and fetching account details again to confirm...")
    time.sleep(10)
    final_account_res = client.get_account_v3()
    print("\n--- Final Account Details ---")
    print(final_account_res)
    print("-----------------------------\n")
    print("Registration process complete.")

except Exception as e:
    print(f"An error occurred: {e}")
