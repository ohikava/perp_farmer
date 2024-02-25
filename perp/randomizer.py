import random 
import perp.config as config
import perp.constants as constants


class Randomizer:
    def get_random_time(self):
        return random.randrange(config.MIN_POSITION_TIME, config.MAX_POSITION_TIME)
    
    def get_random_sides(self):
        return random.choice([constants.LONG_AEVO_SHORT_HYPERLIQUID, constants.SHORT_AEVO_LONG_HYPERLIQUID])

    def get_random_leverage(self):
        return random.randrange(config.MIN_LEVERAGE, config.MAX_LEVERAGE)
    
    def get_random_coin(self):
        return random.choice(config.COINS)
    