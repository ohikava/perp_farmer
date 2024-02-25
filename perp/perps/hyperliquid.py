import perp.config as config 
import perp.constants as constants 
from perp.utils.hyperliquid_types import Cloid, Meta
from perp.utils.hyperliquid_api import API
from perp.utils.hyperliquid_signing import OrderType, OrderRequest, OrderWire, \
                                        get_timestamp_ms, order_request_to_order_wire, order_wires_to_order_action, \
                                        sign_l1_action
import eth_account
import logging 
from typing import Optional, Any, List, cast
import time 
import os 
from dotenv import load_dotenv

load_dotenv()




logger = logging.getLogger(__name__)


class Hyperliquid(API):
    def __init__(self):
        super().__init__()
        self.wallet = eth_account.Account.from_key(os.getenv("HYPERLIQUID_PRIVATE_KEY"))
        self.vault_address = None
        
        self.meta = self.meta()
        self.coin_to_asset = {asset_info["name"]: asset for (asset, asset_info) in enumerate(self.meta["universe"])}

    def market_open(
        self,
        coin: str,
        is_buy: bool,
        sz: float,
        px: Optional[float] = None,
        slippage: float = config.HL_SLIPPAGE,
        cloid: Optional[Cloid] = None,
    ) -> Any:

        # Get aggressive Market Price
        px = self._slippage_price(coin, is_buy, slippage, px)
        # Market Order is an aggressive Limit Order IoC
        return self.order(coin, is_buy, sz, px, order_type={"limit": {"tif": "Ioc"}}, reduce_only=False, cloid=cloid)
    
    def order(
        self,
        coin: str,
        is_buy: bool,
        sz: float,
        limit_px: float,
        order_type: OrderType,
        reduce_only: bool = False,
        cloid: Optional[Cloid] = None,
    ) -> Any:
        order: OrderRequest = {
            "coin": coin,
            "is_buy": is_buy,
            "sz": sz,
            "limit_px": limit_px,
            "order_type": order_type,
            "reduce_only": reduce_only,
        }
        if cloid:
            order["cloid"] = cloid
        return self.bulk_orders([order])
    
    def bulk_orders(self, order_requests: List[OrderRequest]) -> Any:
        order_wires: List[OrderWire] = [
            order_request_to_order_wire(order, self.coin_to_asset[order["coin"]]) for order in order_requests
        ]
        timestamp = get_timestamp_ms()

        order_action = order_wires_to_order_action(order_wires)

        signature = sign_l1_action(
            self.wallet,
            order_action,
            timestamp,
        )

        return self._post_action(
            order_action,
            signature,
            timestamp,
        )
    
    def _post_action(self, action, signature, nonce):
        payload = {
            "action": action,
            "nonce": nonce,
            "signature": signature,
            "vaultAddress": None,
        }
        logging.debug(payload)
        return self.post("/exchange", payload)
    
    def meta(self) -> Meta:
        return cast(Meta, self.post("/info", {"type": "meta"}))
    
    def all_mids(self) -> dict:
        return self.post("/info", {"type": "allMids"})
        
    def _slippage_price(
        self,
        coin: str,
        is_buy: bool,
        slippage: float,
        px: Optional[float] = None,
    ) -> float:

        if not px:
            # Get midprice
            px = float(self.all_mids()[coin])
        # Calculate Slippage
        px *= (1 + slippage) if is_buy else (1 - slippage)
        # We round px to 5 significant figures and 6 decimals
        return round(float(f"{px:.5g}"), 6)