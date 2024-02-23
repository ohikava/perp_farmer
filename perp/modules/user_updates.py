import logging
import perp.constants as constants

logger = logging.getLogger(__name__)

class UserUpdates:
    def subscribe_all_perps(self):
        self.hyperliquid.subscribe_user_state(self.hyperliquid_acc_update)
        
    def hyperliquid_acc_update(self, payload):
        fills = payload['data'].get('fills', [])

        fills = [
            {
                "side": constants.LONG if fill['side'] == 'B' else constants.SHORT,
                "fee": fill['fee'],
                "size": fill['sz'],
                "price": fill['px'],
                "coin": fill['coin']
            }
            for fill in fills 
        ]

        if not fills:
            return 
        
        for fill in fills:
            coin = fill.get('coin', None)