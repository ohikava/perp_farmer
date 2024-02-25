from perp.perps.aevo import Aevo
from perp.perps.drift import Drift
from perp.perps.hyperliquid import Hyperliquid
from perp.modules.user_updates import UserUpdates
from perp.randomizer import Randomizer
import perp.config as config
import json 

pk = json.load(open("pk.json"))


class Main(UserUpdates):
    def __init__(self):
        self.aevo = Aevo()
        # self.drift = Drift(private_key=pk['DRIFT_PROTOCOL_PK'])
        self.hyperliquid = Hyperliquid()

        self.randomizer = Randomizer()
    
    def run(self):
        pass 