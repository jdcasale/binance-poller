import logging
import time
import requests
import base64
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

from utils.config import Config

BINANCE_API_URL = "https://testnet.binance.vision/"
ENDPOINT = "/api/v3/account"
config = Config()

# Load the Ed25519 private key from a PEM file
def load_private_key() -> Ed25519PrivateKey:
    with open(config.get_ed25519_secret_path(), 'rb') as key_file:
        private_key = serialization.load_pem_private_key(key_file.read(), password=None)
    return private_key

# Create a signature using the Ed25519 private key
def create_signature(private_key: Ed25519PrivateKey, message: str) -> str:
    signature = private_key.sign(message.encode('utf-8'))
    return base64.b64encode(signature).decode('utf-8')

# Make a signed request to the Binance API using Ed25519 keys
def get_account_info() -> dict:
    # Load the private key
    private_key = load_private_key()

    # Prepare the query string (timestamp is required for signed requests)
    timestamp = int(time.time() * 1000)
    query_string = f"timestamp={timestamp}"

    # Create the signature using the Ed25519 private key
    signature = create_signature(private_key, query_string)

    # Headers
    headers = {
        'X-MBX-APIKEY': config.get_ed25519_api_key(),
    }

    # Full URL with signature
    url = f"{BINANCE_API_URL}{ENDPOINT}?{query_string}&signature={signature}"

    # Send the GET request
    response = requests.get(url, headers=headers)

    # Handle the response
    if response.status_code == 200:
        logging.debug("Account Information:", response.json())
        resp_info = response.json()
        return resp_info
    else:
        print(f"Error: {response.status_code}, {response.text}")

# Example usage
if __name__ == "__main__":
    get_account_info()
