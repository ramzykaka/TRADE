from binance.client import Client

class BinanceAPI:
    def __init__(self, api_key, api_secret):
        self.client = Client(api_key, api_secret)
    
    def get_balance(self, asset='USDT'):
        return self.client.get_asset_balance(asset=asset)