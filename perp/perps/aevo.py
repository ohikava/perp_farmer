import asyncio
import json
import random
import time
import traceback

import requests
import websockets
from eth_account import Account
from eth_hash.auto import keccak
from web3 import Web3
import os 
import perp.config as config 
from dotenv import load_dotenv
from perp.utils.eip712_structs import Address, Boolean, EIP712Struct, Uint, make_domain
import perp.constants as constants
from typing import Optional

load_dotenv()

API_KEY = os.getenv("AEVO_API_KEY")
API_SECRET = os.getenv("AEVO_API_SECRET")
SIGN_KEY = os.getenv("AEVO_SIGN_KEY")
WALLET_ADDRESS = os.getenv("AEVO_WALLET_ADDRESS")

CONFIG = {
    "mainnet": {
        "rest_url": "https://api.aevo.xyz",
        "ws_url": "wss://ws.aevo.xyz",
        "signing_domain": {
            "name": "Aevo Mainnet",
            "version": "1",
            "chainId": "1",
        },
    },
}


class Order(EIP712Struct):
    maker = Address()
    isBuy = Boolean()
    limitPrice = Uint(256)
    amount = Uint(256)
    salt = Uint(256)
    instrument = Uint(256)
    timestamp = Uint(256)


instrument_ids = {
    'ETH': 1,
    'SOL': 5197,
    'BTC': 3396
}

class Aevo:
    def __init__(
        self,
        env="mainnet",
        rest_headers={},
    ):
        self.signing_key = SIGN_KEY
        self.wallet_address = WALLET_ADDRESS
        self.api_key = API_KEY
        self.api_secret = API_SECRET

        self.client = requests
        self.rest_headers = {
            "AEVO-KEY": self.api_key,
            "AEVO-SECRET": self.api_secret,
        }
        self.extra_headers = None
        self.rest_headers.update(rest_headers)

        if (env != "testnet") and (env != "mainnet"):
            raise ValueError("env must either be 'testnet' or 'mainnet'")
        self.env = env

    @property
    def address(self):
        return Account.from_key(self.signing_key).address

    @property
    def rest_url(self):
        return CONFIG[self.env]["rest_url"]

    @property
    def signing_domain(self):
        return CONFIG[self.env]["signing_domain"]

    # Public REST API
    def get_index(self, asset):
        req = self.client.get(f"{self.rest_url}/index?asset={asset}")
        data = req.json()
        return data

    def get_markets(self, asset):
        req = self.client.get(f"{self.rest_url}/markets?asset={asset}")
        data = req.json()
        return data

    # Private REST API
    def rest_create_order(
        self, instrument_id, is_buy, limit_price, quantity, post_only=True
    ):
        data, order_id = self.create_order_rest_json(
            int(instrument_id), is_buy, limit_price, quantity, post_only
        )
        req = self.client.post(
            f"{self.rest_url}/orders", json=data, headers=self.rest_headers
        )
        try:
            return req.json()
        except:
            return req.text()

    def rest_create_market_order(self, instrument_id, is_buy, quantity):
        limit_price = 0
        if is_buy:
            limit_price = 10*6 - 1

        data, order_id = self.create_order_rest_json(
            int(instrument_id),
            is_buy,
            limit_price,
            quantity,
            post_only=False,
        )

        req = self.client.post(
            f"{self.rest_url}/orders", json=data, headers=self.rest_headers
        )
        return req.json()

    def rest_cancel_order(self, order_id):
        req = self.client.delete(
            f"{self.rest_url}/orders/{order_id}", headers=self.rest_headers
        )
        return req.json()

    def rest_get_account(self):
        req = self.client.get(f"{self.rest_url}/account", headers=self.rest_headers)
        return req.json()

    def rest_get_portfolio(self):
        req = self.client.get(f"{self.rest_url}/portfolio", headers=self.rest_headers)
        return req.json()

    def rest_get_open_orders(self):
        req = self.client.get(
            f"{self.rest_url}/orders", json={}, headers=self.rest_headers
        )
        return req.json()

    def rest_cancel_all_orders(
        self,
        instrument_type=None,
        asset=None,
    ):
        body = {}
        if instrument_type:
            body["instrument_type"] = instrument_type

        if asset:
            body["asset"] = asset

        req = self.client.delete(
            f"{self.rest_url}/orders-all", json=body, headers=self.rest_headers
        )
        return req.json()
    
    def create_order_rest_json(
        self,
        instrument_id,
        is_buy,
        limit_price,
        quantity,
        post_only=True,
        reduce_only=False,
        close_position=False,
        price_decimals=10**6,
        amount_decimals=10**6,
        trigger=None,
        stop=None,
    ):
        timestamp = int(time.time())
        salt, signature, order_id = self.sign_order(
            instrument_id=instrument_id,
            is_buy=is_buy,
            limit_price=limit_price,
            quantity=quantity,
            timestamp=timestamp,
            price_decimals=price_decimals,
        )
        payload = {
            "maker": self.wallet_address,
            "is_buy": is_buy,
            "instrument": instrument_id,
            "limit_price": str(int(round(limit_price * price_decimals, is_buy))),
            "amount": str(int(round(quantity * amount_decimals, is_buy))),
            "salt": str(salt),
            "signature": signature,
            "post_only": post_only,
            "reduce_only": reduce_only,
            "close_position": close_position,
            "timestamp": timestamp,
        }
        if trigger and stop:
            payload["trigger"] = trigger
            payload["stop"] = stop

        return payload, order_id

    def sign_order(
        self,
        instrument_id,
        is_buy,
        limit_price,
        quantity,
        timestamp,
        price_decimals=10**6,
        amount_decimals=10**6,
    ):
        salt = random.randint(0, 10**10)  # We just need a large enough number

        order_struct = Order(
            maker=self.wallet_address,  # The wallet"s main address
            isBuy=is_buy,
            limitPrice=int(round(limit_price * price_decimals, is_buy)),
            amount=int(round(quantity * amount_decimals, is_buy)),
            salt=salt,
            instrument=instrument_id,
            timestamp=timestamp,
        )
        domain = make_domain(**self.signing_domain)
        signable_bytes = keccak(order_struct.signable_bytes(domain=domain))
        return (
            salt,
            Account._sign_hash(signable_bytes, self.signing_key).signature.hex(),
            f"0x{signable_bytes.hex()}",
        )
    
    def _slippage_price(
        self,
        coin: str,
        is_buy: bool,
        slippage: float,
        px: Optional[float] = None,
    ) -> float:
        if not px:
            px = float(self.get_index(coin)['price'])
        px *= (1 + slippage) if is_buy else (1 - slippage)
        return round(float(f"{px:.5g}"), config.AEVO_PRICE_DECIMALS[coin])
    
    def buy_market_order(self, coin, sz):
        price = self._slippage_price(coin, True, config.AEVO_SLIPPAGE)
        res = self.rest_create_order(instrument_ids[coin], True, price, sz, post_only=False)
        
        return {
            "px": res.get("price", price),
            "sz": res.get("amount", sz),
            "order_status": res.get("status", "failed"),
            "side": constants.LONG if res.get('side', 'buy') == 'buy' else constants.SHORT,
            'coin': coin 
        } 

    def sell_market_order(self, coin, sz):
        price = self._slippage_price(coin, False, config.AEVO_SLIPPAGE)
        res = self.rest_create_order(instrument_ids[coin], False, price, sz, post_only=False)
        
        return {
            "px": res.get("price", price),
            "sz": res.get("amount", sz),
            "order_status": res.get("order_status", "failed"),
            "side": constants.LONG if res.get('side', 'buy') == 'buy' else constants.SHORT,
            'coin': coin 
        } 
        