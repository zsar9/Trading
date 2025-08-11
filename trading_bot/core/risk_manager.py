"""
Risk manager: position sizing, stop loss, take profit, exposure constraints.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Optional


logger = logging.getLogger(__name__)


@dataclass
class OrderRequest:
    symbol: str
    side: str  # buy/sell
    order_type: str  # market/limit
    quantity: float
    price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    time_in_force: str = "day"


class RiskManager:
    def __init__(self, config: Dict):
        self.config = config
        self.risk_cfg = config.get("risk", {})

    def compute_position_size(self, price: float, account_equity: float) -> float:
        max_position_pct = float(self.risk_cfg.get("max_position_pct_of_capital", 10)) / 100.0
        fixed_risk = self.risk_cfg.get("fixed_risk_dollars")
        max_dollars = account_equity * max_position_pct
        if fixed_risk is not None:
            max_dollars = min(max_dollars, float(fixed_risk))
        if price <= 0:
            return 0.0
        qty = max_dollars / price
        return max(qty, 0.0)

    def apply_stops(self, side: str, entry_price: float) -> (Optional[float], Optional[float]):
        stop_loss = None
        take_profit = None
        sl_cfg = self.risk_cfg.get("stop_loss", {})
        tp_cfg = self.risk_cfg.get("take_profit", {})
        if sl_cfg.get("enabled", True) and sl_cfg.get("method") == "percent":
            pct = float(sl_cfg.get("value_pct", 1.5)) / 100.0
            stop_loss = entry_price * (1 - pct) if side == "buy" else entry_price * (1 + pct)
        if tp_cfg.get("enabled", True) and tp_cfg.get("method") == "reward:risk":
            rr = float(tp_cfg.get("rr_ratio", 2.0))
            if stop_loss is not None:
                risk_per_unit = abs(entry_price - stop_loss)
                reward = risk_per_unit * rr
                take_profit = entry_price + reward if side == "buy" else entry_price - reward
        return stop_loss, take_profit

    def approve_order(self, symbol: str, side: str, price: float, equity: float) -> Optional[OrderRequest]:
        qty = self.compute_position_size(price, equity)
        if qty <= 0:
            logger.info("Risk blocked order: zero position size for %s", symbol)
            return None
        sl, tp = self.apply_stops(side, price)
        return OrderRequest(symbol=symbol, side=side, order_type="market", quantity=qty, price=price, stop_loss=sl, take_profit=tp)