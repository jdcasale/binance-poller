import tomllib
from typing import List

class Config:
    def __init__(self, config_file: str = 'config.toml') -> None:
        # Load the config file
        with open(config_file, 'rb') as f:
            self.config = tomllib.load(f)

    def get_api_key(self) -> str:
        """Returns the Binance API key."""
        return self.config['binance']['api_key']

    def get_api_secret(self) -> str:
        """Returns the Binance API secret."""
        return self.config['binance']['api_secret']

    def get_polling_interval(self) -> int:
        """Returns the polling interval."""
        return self.config['binance'].get('polling_interval', 30)

    def get_log_level(self) -> str:
        """Returns the desired runtime logging level."""
        return self.config['logging'].get('log_level', 'INFO')

    def get_ed25519_api_key(self) -> str:
        """
        Returns an ed25519 API key.
        Currently, the python-binance library does not support ed25519_api_keys,
        but the account_info API can only be accessed with an API key generated from one.
        Thus, we need this temporary workaround until the libary adds support for this.
        """
        return self.config['binance']['api_key_ed25519']

    def get_ed25519_secret_path(self) -> str:
        """Returns a local path to an ed25519 secret key for signing requests."""
        return self.config['binance']['ed25519_secret_key_path']

    def get_web_host(self) -> str:
        """Returns a host for configuring the web server."""
        return self.config['web-server'].get('host', '0.0.0.0')

    def get_web_port(self) -> str:
        """Returns a host for configuring the web server."""
        return self.config['web-server'].get('port', 8000)

# Example of how to use the Config class:
if __name__ == "__main__":
    config = Config()
    print("API Key:", config.get_api_key())
    print("API Secret:", config.get_api_secret())
    print("Polling Interval:", config.get_polling_interval())
    print("Symbols:", config.get_symbols_list())
