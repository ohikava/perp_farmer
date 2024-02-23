from perp.perps.aevo import Aevo
from perp.perps.drift import Drift
from perp.perps.hyperliquid import Hyperliquid

class Main:
    def __init__(self):
        self.aevo = Aevo()
        self.drift = Drift()
        self.hyperliquid = Hyperliquid()

        self.perps = [self.aevo, self.drift, self.hyperliquid]

    def run(self):
        pass 