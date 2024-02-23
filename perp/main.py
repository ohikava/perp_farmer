from perp.perps.aevo import Aevo
from perp.perps.drift import Drift
from perp.perps.hyperliquid import Hyperliquid
import perp.config as config
import json 

pk = json.load(open("pk.json"))


class Main:
    def __init__(self):
        self.aevo = Aevo(private_key=pk['AEVO_PK'])
        self.drift = Drift(private_key=pk['DRIFT_PROTOCOL_PK'])
        self.hyperliquid = Hyperliquid(private_key=pk['HYPERLIQUID_PK'])

        self.perps = [self.aevo, self.drift, self.hyperliquid]

    def run(self):
        pass 