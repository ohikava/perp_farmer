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