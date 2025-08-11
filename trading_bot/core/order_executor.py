"""
Order executor: routes orders to broker (paper or live).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Optional
from datetime import datetime, timezone


logger = logging.getLogger(__name__)


@dataclass
class Fill:
    symbol: str
    side: str
    quantity: float
    price: float
    timestamp: datetime
    broker: str


class PaperBroker:
    def __init__(self, slippage_pct: float = 0.0, commission: float = 0.0):
        self.slippage_pct = slippage_pct
        self.commission = commission

    def submit_market(self, symbol: str, side: str, quantity: float, ref_price: float) -> Fill:
        effective_price = ref_price * (1 + self.slippage_pct * (1 if side == "buy" else -1))
        ts = datetime.now(tz=timezone.utc)
        logger.info("Paper fill %s %s qty=%.4f @ %.4f", side, symbol, quantity, effective_price)
        return Fill(symbol=symbol, side=side, quantity=quantity, price=effective_price, timestamp=ts, broker="paper")


class OrderExecutor:
    def __init__(self, config: Dict):
        self.config = config
        exec_cfg = config.get("execution", {})
        slippage = 0.0
        model = exec_cfg.get("slippage_model", {})
        if model.get("type") == "percent":
            slippage = float(model.get("value", 0.0)) / 100.0
        commission = float(config.get("backtest", {}).get("commission_per_trade", 0.0))
        self.paper = PaperBroker(slippage_pct=slippage, commission=commission)
        self.live_broker = None  # Placeholder for live broker integration

    def submit_order(self, symbol: str, side: str, quantity: float, price: float, live: bool = False) -> Fill:
        if live:
            # TODO: Implement Alpaca/IB live order routing using credentials from config
            logger.warning("Live execution not implemented; routing to paper.")
        return self.paper.submit_market(symbol, side, quantity, ref_price=price)