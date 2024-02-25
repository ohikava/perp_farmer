import random 
import perp.config as config


class Randomizer:
    def get_random_time(self):
        return random.randrange(config.MIN_POSITION_TIME, config.MAX_POSITION_TIME)