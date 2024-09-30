import asyncio
import time
from binance import AsyncClient, BinanceSocketManager
from binance.exceptions import BinanceAPIException, BinanceRequestException
from typing import Optional
from cryptography.hazmat.primitives.serialization import load_pem_private_key


from publishing.core import FilePubSub, KeyValueStorePubSub, InMemoryWithLogPublisher
from storage.core import KeyValueStorage, InMemoryKeyValueStorage
from utils import account_info_workaround
from utils.config import Config
from utils.logging import setup_logging


class BinanceExchangeMetadataPoller:
    def __init__(self, config: Config, key_value_storage: KeyValueStorage):
        self.config = config
        self.logger = setup_logging(__name__)
        self.api_key = config.get_api_key()
        self.api_secret = config.get_api_secret()
        self.ed_api_key = config.get_ed25519_api_key()
        self.secret_key_path = config.get_ed25519_secret_path()
        self.polling_interval = config.get_polling_interval()
        file_pub = FilePubSub(flush_interval=5.0, flush_limit=10)
        kvs_pub = KeyValueStorePubSub(key_value_storage)
        self.publisher = InMemoryWithLogPublisher(kvs_pub, file_pub)
        self.client = None
        self.socket_manager = None
        self.private_key = None

    async def initialize(self):
        """
        Initialize the Binance client, load the private key, and set up socket manager.
        """
        with open(self.secret_key_path, 'rb') as f:
            self.private_key = load_pem_private_key(data=f.read(), password=None)

        self.logger.info("Initializing poller...")
        self.client = await AsyncClient.create(self.api_key, self.api_secret)
        self.socket_manager = BinanceSocketManager(self.client)
        await self.start_polling()

    async def start_polling(self):
        """
        Start polling HTTP endpoints and WebSocket ticker streams.
        """

        http_task = asyncio.create_task(self.poll_http_endpoints())

        await asyncio.gather(http_task)

        await self.client.close_connection()
        await self.publisher.close()


    @staticmethod
    def condition_to_refresh_metadata(ticker_update):
        """
        Define conditions under which you should refresh exchange metadata.
        """
        return 'status' in ticker_update and ticker_update['status'] == 'BREAK'

    async def poll_http_endpoints(self):
        """
        Poll non-time-sensitive data using HTTP APIs.
        """
        while True:
            self.logger.debug(f"Polling HTTP endpoints at {time.strftime('%Y-%m-%d %H:%M:%S')}")

            exchange_info = await self.get_exchange_info()
            if exchange_info:
                self.publisher.publish(topic='exchange_info', message=exchange_info)

            account_info = self.get_account_info()
            if account_info:
                self.publisher.publish(topic='account_info', message=account_info)

            system_status = await self.get_system_status()
            if system_status:
                self.publisher.publish(topic='system_status', message=system_status)

            self.logger.debug(f"Sleeping for {self.polling_interval} seconds...")
            await asyncio.sleep(self.polling_interval)

    async def get_exchange_info(self) -> Optional[dict]:
        """
        Fetch exchange metadata including symbol info and rate limits.
        """
        try:
            self.logger.debug('Fetching exchange info')
            exchange_info = await self.client.get_exchange_info()
            return exchange_info
        except (BinanceAPIException, BinanceRequestException) as e:
            self.logger.error(f"Error fetching exchange info: {e}")
            return None

    async def get_symbol_info(self, symbol: str) -> Optional[dict]:
        """
        Fetch exchange metadata for a specific symbol.
        """
        try:
            self.logger.debug(f'Fetching symbol info for symbol {symbol}')
            exchange_info = await self.client.get_symbol_info(symbol)
            return exchange_info
        except (BinanceAPIException, BinanceRequestException) as e:
            self.logger.error(f"Error fetching symbol info: {e}")
            return None

    def get_account_info(self) -> Optional[dict]:
        """
        Fetch account balances and permissions.
        """
        try:
            self.logger.debug('Fetching account info')
            return account_info_workaround.get_account_info()

        except (BinanceAPIException, BinanceRequestException) as e:
            self.logger.error(f"Error fetching account info: {e}")
            return None

    async def get_system_status(self) -> Optional[dict]:
        """
        Fetch deposit and withdrawal system status.
        """
        try:
            status = await self.client.get_system_status()
            return status
        except (BinanceAPIException, BinanceRequestException) as e:
            self.logger.error(f"Error fetching system status: {e}")
            return None


async def main():
    """
    Main entry point to run the poller.
    """
    config = Config()
    kvs = InMemoryKeyValueStorage()
    poller = BinanceExchangeMetadataPoller(config, kvs)
    await poller.initialize()


if __name__ == "__main__":
    asyncio.run(main())
