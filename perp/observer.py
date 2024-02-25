import logging 
import requests 

logger = logging.getLogger(__name__)

client_id=-1002005413825
token = "6827720178:AAGORl7Nu7jFItPuPQ5O3dXRmiiTWPluD5M"

class Observer:
    def send_sync_message(self, msg):
        uri = f"https://api.telegram.org/bot{token}/sendMessage"
    
        body = {
            "chat_id": client_id,
            "text": msg
        }

        requests.post(uri, json=body)
    
    def order_filled(self, order_info, order_type):
        logger_msg = f"{order_info['perp']} {order_info['side']} {order_info['coin']} sz {order_info['sz']} px {order_info['px']} tp {order_type} filled"
        logger.info(logger_msg)
        self.send_sync_message(logger_msg)

    def show_stats(self, aevo_fees, hyperliquid_fees, aevo_profit, hyperliquid_profit):
        logger_msg = f"aevo fees {aevo_fees}$ hyperliquid fees {hyperliquid_fees}$ aevo profit {aevo_profit}$ hyperliquid profit {hyperliquid_profit}$ total {aevo_profit + hyperliquid_profit - aevo_fees - hyperliquid_fees}$"
        logger.info(logger_msg)
        tg_msg = f"aevo fees: {aevo_fees}$\nhl fees: {hyperliquid_fees}$\naevo profit: {aevo_profit}$\nhl profit: {hyperliquid_profit}$\ntotal: {round(aevo_profit + hyperliquid_profit - aevo_fees - hyperliquid_fees, 2)}$"
        self.send_sync_message(tg_msg)