from perp.perps.aevo import Aevo
from perp.perps.hyperliquid import Hyperliquid
from perp.randomizer import Randomizer
from perp.observer import Observer
from perp.utils.funcs import calculate_profit
import perp.config as config
import perp.constants as constants
import json 
import threading
import time 


class Main():
    def __init__(self):
        self.aevo = Aevo()
        self.hyperliquid = Hyperliquid()

        self.randomizer = Randomizer()

        self.positions_aevo = {}
        self.positions_hyperliquid = {}

        self.observer = Observer()
        self.positions_total = []
    
    def run(self):
        while True:
            self.check_should_close_position() 

            if not self.positions_aevo and not self.positions_hyperliquid:
                self.open_position()
    
    def check_should_close_position(self):
        if not self.positions_aevo or not self.positions_hyperliquid:
            return
        

        coin = list(self.positions_aevo.keys())[0]
        aevo_position = self.positions_aevo[coin]
        hyperliquid_position = self.positions_hyperliquid[coin]

        fill_time = min(aevo_position["fill_time"], hyperliquid_position["fill_time"])

        if time.time() - fill_time < aevo_position["position_lifetime"]:
            return

        self.close_position(coin)

    def open_position(self):
        coin = self.randomizer.get_random_coin()
        leverage = self.randomizer.get_random_leverage()
        sides = self.randomizer.get_random_sides()
        position_lifetime = self.randomizer.get_random_time()

        mid_price = self.hyperliquid.get_mid_price(coin)
        position_size = config.POSITION_SIZE / mid_price

        scaled_position_size = position_size * leverage
        min_decimals = min(config.AEVO_SIZE_DECIMALS[coin], config.HL_SIZE_DECIMALS[coin])
        scaled_position_size = round(scaled_position_size, min_decimals)

        threads = []
        if sides == constants.LONG_AEVO_SHORT_HYPERLIQUID:
            threads.append(threading.Thread(target=self.aevo.market_buy, args=(coin, scaled_position_size)))
            threads.append(threading.Thread(target=self.hyperliquid.market_sell, args=(coin, scaled_position_size)))
        else:
            threads.append(threading.Thread(target=self.aevo.market_sell, args=(coin, scaled_position_size)))
            threads.append(threading.Thread(target=self.hyperliquid.market_buy, args=(coin, scaled_position_size)))
        
        for t in threads:
            t.start()

        for t in threads:
            t.join()

        time.sleep(config.SLEEP)

        self.positions_aevo[coin] = {**self.aevo.last_fill, "position_lifetime": position_lifetime}
        self.observer.order_filled(self.aevo.last_fill, 'OPEN')

        self.positions_hyperliquid[coin] = {**self.hyperliquid.last_fill, "position_lifetime": position_lifetime}
        self.observer.order_filled(self.hyperliquid.last_fill, 'OPEN')

        print(self.positions_aevo, self.positions_hyperliquid)
    
    def close_position(self, coin):
        if coin not in self.positions_aevo or coin not in self.positions_hyperliquid:
            return
        
        aevo_position = self.positions_aevo[coin]
        hyperliquid_position = self.positions_hyperliquid[coin]

        threads = []

        if aevo_position["side"] == constants.LONG:
            threads.append(threading.Thread(target=self.aevo.market_sell, args=(coin, aevo_position["sz"])))
            threads.append(threading.Thread(target=self.hyperliquid.market_buy, args=(coin, hyperliquid_position["sz"])))
        else:
            threads.append(threading.Thread(target=self.aevo.market_buy, args=(coin, aevo_position["sz"])))
            threads.append(threading.Thread(target=self.hyperliquid.market_sell, args=(coin, hyperliquid_position["sz"])))
        
        for t in threads:
            t.start()

        for t in threads:
            t.join()

        time.sleep(config.SLEEP)

        self.observer.order_filled(self.aevo.last_fill, 'CLOSE')
        
        self.observer.order_filled(self.hyperliquid.last_fill, 'CLOSE')

        total = {
            "aevo_profit": calculate_profit(aevo_position, self.aevo.last_fill),
            "hyperliquid_profit": calculate_profit(hyperliquid_position, self.hyperliquid.last_fill),
            "aevo_fees": self.aevo.last_fill["fee"] + aevo_position["fee"],
            "hyperliquid_fees": self.hyperliquid.last_fill["fee"] + hyperliquid_position["fee"]
        }
        self.positions_total.append(total)
        
        self.positions_aevo.pop(coin)
        self.positions_hyperliquid.pop(coin)

        self.calculate_stats()
    
    def calculate_stats(self):
        aevo_fees = 0.0
        hyperliquid_fees = 0.0

        aevo_profit = 0.0
        hyperliquid_profit = 0.0

        for deal in self.positions_total:
            aevo_fees += deal["aevo_fees"]
            hyperliquid_fees += deal["hyperliquid_fees"]

            aevo_profit += deal["aevo_profit"]
            hyperliquid_profit += deal["hyperliquid_profit"]
        
        self.observer.show_stats(round(aevo_fees, 2), round(hyperliquid_fees, 2), round(aevo_profit, 2), round(hyperliquid_profit, 2))
        

