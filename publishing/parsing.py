def parse_symbols_info(response: dict) -> dict:
    """
    Parse Binance exchangeInfo response to extract relevant metadata for each symbol.
    """

    symbol_metadata = {}

    for symbol_info in response.get("symbols", []):
        symbol = symbol_info.get("symbol")
        status = symbol_info.get("status")
        base_asset = symbol_info.get("baseAsset")
        quote_asset = symbol_info.get("quoteAsset")

        # Initialize variables for metadata
        tick_size = None
        min_price = None
        max_price = None
        min_qty = None
        max_qty = None
        step_size = None

        # Loop through filters to extract PRICE_FILTER and LOT_SIZE
        for filter_info in symbol_info.get("filters", []):
            if filter_info.get("filterType") == "PRICE_FILTER":
                min_price = filter_info.get("minPrice")
                max_price = filter_info.get("maxPrice")
                tick_size = filter_info.get("tickSize")
            elif filter_info.get("filterType") == "LOT_SIZE":
                min_qty = filter_info.get("minQty")
                max_qty = filter_info.get("maxQty")
                step_size = filter_info.get("stepSize")

        symbol_metadata[symbol] = {
            "symbol": symbol,
            "baseAsset": base_asset,
            "quoteAsset": quote_asset,
            "tickSize": tick_size,
            "minPrice": min_price,
            "maxPrice": max_price,
            "lotSize": {
                "minQty": min_qty,
                "maxQty": max_qty,
                "stepSize": step_size
            },
            "status": status
        }

    return symbol_metadata

# Example usage with mock response
# sample_response = {
#     "symbols": [
#         {
#             "symbol": "BTCUSDT",
#             "status": "TRADING",
#             "baseAsset": "BTC",
#             "quoteAsset": "USDT",
#             "filters": [
#                 {
#                     "filterType": "PRICE_FILTER",
#                     "minPrice": "10000.00000000",
#                     "maxPrice": "100000.00000000",
#                     "tickSize": "0.01000000"
#                 },
#                 {
#                     "filterType": "LOT_SIZE",
#                     "minQty": "0.00100000",
#                     "maxQty": "100.00000000",
#                     "stepSize": "0.00100000"
#                 }
#             ]
#         }
#     ]
# }
#
# metadata = parse_symbols_info(sample_response)
# print(json.dumps(metadata, indent=2))
