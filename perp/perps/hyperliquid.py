import perp.config as config 
from hyperliquid.exchange import Exchange
from hyperliquid.utils.constants import MAINNET_API_URL
import eth_account
import logging 

logger = logging.getLogger(__name__)



class Hyperliquid:
    def __init__(self, private_key):
        self.account = eth_account.Account.from_key(private_key)
        self.exchange = Exchange(self.account, MAINNET_API_URL)

        logger.info(f"Hyperliquid initialized with address: {self.account.address}")

    def buy_order(self, coin, sz, px, side):
        pass

    def sell_order(self, coin, sz, px, side):
        pass

    def take_profit(self, coin, sz, px, side):
        pass

    def stop_loss(self, coin, sz, px, side):
        pass

    def load_prices(self, coin):
        pass