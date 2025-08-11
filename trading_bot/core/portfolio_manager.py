"""
Portfolio manager: tracks cash, positions, PnL, and applies allocation constraints.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict

logger = logging.getLogger(__name__)


@dataclass
class Position:
    symbol: str
    quantity: float = 0.0
    avg_price: float = 0.0


@dataclass
class Portfolio:
    cash: float
    positions: Dict[str, Position] = field(default_factory=dict)

    def equity(self, prices: Dict[str, float]) -> float:
        market_value = sum(pos.quantity * prices.get(sym, pos.avg_price) for sym, pos in self.positions.items())
        return self.cash + market_value

    def apply_fill(self, symbol: str, side: str, qty: float, price: float) -> None:
        pos = self.positions.get(symbol, Position(symbol))
        if side == "buy":
            new_qty = pos.quantity + qty
            if new_qty > 0:
                pos.avg_price = (pos.quantity * pos.avg_price + qty * price) / new_qty
            pos.quantity = new_qty
            self.cash -= qty * price
        elif side == "sell":
            pos.quantity -= qty
            self.cash += qty * price
            if pos.quantity <= 0:
                pos.avg_price = 0.0
        self.positions[symbol] = pos
        logger.info("Updated position %s: qty=%.4f avg=%.4f; cash=%.2f", symbol, pos.quantity, pos.avg_price, self.cash)