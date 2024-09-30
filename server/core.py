import asyncio

import uvicorn
from fastapi import FastAPI, HTTPException

from poller.core import BinanceExchangeMetadataPoller
from storage.core import KeyValueStorage, InMemoryKeyValueStorage
from utils.config import Config


class ExchangeMetadataWebServer:
    def __init__(self, kv_store: KeyValueStorage):
        self.kv_store = kv_store
        self.app = FastAPI()


        @self.app.get("/rate_limits")
        async def get_rate_limits():
            """
            Get rate limit info
            """
            data = self.kv_store.read('exchange_info', 'rateLimits')
            if data is None:
                raise HTTPException(status_code=404, detail="No data available")
            return data
        @self.app.get("/symbols")
        async def get_symbols():
            """
            Get a list of symbols active on the exchange
            """
            all_symbol_data = self.kv_store.read_all('symbols')
            if all_symbol_data is None:
                raise HTTPException(status_code=404, detail="No data available")
            return {"symbols": list(all_symbol_data.keys())}

        # Define API routes
        @self.app.get("/symbols/{symbol}")
        async def get_symbol_info(symbol: str):
            """
            Get reference information for a specific symbol
            """
            symbol_data = self.kv_store.read('symbols', symbol)
            if not symbol_data:
                raise HTTPException(status_code=404, detail="Symbol not found")
            return symbol_data

        @self.app.get("/exchange_status")
        async def get_all_exchange_info():
            """
            Get all reference information for all symbols
            """
            data = self.kv_store.read_all('system_status')
            if data is None:
                raise HTTPException(status_code=404, detail="No data available")
            return data


        @self.app.get("/account_info")
        async def get_all_account_info():
            """
            Get account info
            """
            data = self.kv_store.read_all('account_info')
            if data is None:
                raise HTTPException(status_code=404, detail="No data available")
            return data


    def run(self):
        """
        Run the FastAPI server
        """
        uvicorn.run(self.app, host=Config().get_web_host(), port=Config().get_web_port())

async def main():
    config = Config()

    kv_store = InMemoryKeyValueStorage()
    # Start the poller to update exchange info every 60 seconds
    poller = BinanceExchangeMetadataPoller(config, kv_store)
    poller_task = asyncio.create_task(poller.initialize())

    # Set up and run the web server
    server = ExchangeMetadataWebServer(kv_store)

    # Run the web server and poller concurrently
    await asyncio.gather(
        poller_task,
        asyncio.to_thread(server.run)  # FastAPI needs to run in a thread
    )

# Running the server and simulating data polling
if __name__ == "__main__":
    asyncio.run(main())