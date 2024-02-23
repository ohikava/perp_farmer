import perp.config as config 
import perp.constants as constants 
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
from hyperliquid.utils.constants import MAINNET_API_URL
import eth_account
import logging 

logger = logging.getLogger(__name__)



class Hyperliquid:
    def __init__(self, private_key):
        self.account = eth_account.Account.from_key(private_key)
        self.exchange = Exchange(self.account, MAINNET_API_URL)
        self.info = Info(MAINNET_API_URL, skip_ws=False)

        logger.info(f"Hyperliquid initialized with address: {self.account.address}")
    
    def subscribe_user_state(self, cb):
        user_subscription = { "type": "userEvents", "user": str(self.account.address) }

        self.info.subscribe(user_subscription, cb)
        logger.info(f"subscribed for {self.account.address} user events")

    def buy_order(self, coin, sz, px):
        px = round(px * (1 + config.HL_SLIPPAGE), config.HL_DECIMALS[coin])
    
        return self.exchange.order(coin, True, sz, px, {"limit": {"tif": "Gtc"}})

    def sell_order(self, coin, sz, px):
        px = round(px * (1 + config.HL_SLIPPAGE), config.HL_DECIMALS[coin])

        return self.exchange.order(coin, False, sz, px, {"limit": {"tif": "Gtc"}})

    def take_profit(self, coin, sz, px, side, trigger_px):
        trigger_px = round(trigger_px, config.HL_DECIMALS[coin])
        if side == constants.LONG:
            side = True 
        else:
            side = False
        return self.exchange.order(coin, side, sz, px, {"trigger": {"triggerPx": trigger_px, 'isMarket': True, 'tpsl': 'tp'}})

    def stop_loss(self, coin, sz, px, side, trigger_px):
        trigger_px = round(trigger_px, config.HL_DECIMALS[coin])
        if side == constants.LONG:
            side = True 
        else:
            side = False
        return self.exchange.order(coin, side, sz, px, {"trigger": {"triggerPx": trigger_px, 'isMarket': True, 'tpsl': 'sl'}})

    def load_prices(self, coin):
        pass