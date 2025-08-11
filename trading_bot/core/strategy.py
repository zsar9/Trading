"""
Strategy module: defines a strategy interface and concrete strategies.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class Signal:
    symbol: str
    side: str  # "buy" or "sell"
    reason: str
    price: Optional[float]
    timestamp: pd.Timestamp
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    quantity: Optional[float] = None


class Strategy:
    name: str

    def __init__(self, name: str, config: Dict):
        self.name = name
        self.config = config

    def evaluate(self, symbol: str, candles: pd.DataFrame) -> List[Signal]:
        raise NotImplementedError


class EmaCrossoverStrategy(Strategy):
    def __init__(self, config: Dict):
        super().__init__("ema_crossover", config)
        self.fast_period = int(config["strategies"]["ema_crossover"]["fast_period"])
        self.slow_period = int(config["strategies"]["ema_crossover"]["slow_period"])

    def evaluate(self, symbol: str, candles: pd.DataFrame) -> List[Signal]:
        df = candles.copy()
        if len(df) < max(self.fast_period, self.slow_period) + 2:
            return []
        df["ema_fast"] = df["Close"].ewm(span=self.fast_period, adjust=False).mean()
        df["ema_slow"] = df["Close"].ewm(span=self.slow_period, adjust=False).mean()
        df["cross"] = np.sign(df["ema_fast"] - df["ema_slow"]).diff()
        last = df.iloc[-1]
        ts = df.index[-1]
        price = float(last["Close"]) if "Close" in df.columns else None
        signals: List[Signal] = []
        if last["cross"] > 0:
            signals.append(Signal(symbol, "buy", "ema_bullish_cross", price, ts))
        elif last["cross"] < 0:
            signals.append(Signal(symbol, "sell", "ema_bearish_cross", price, ts))
        return signals


class RsiMeanReversionStrategy(Strategy):
    def __init__(self, config: Dict):
        super().__init__("rsi_mean_reversion", config)
        self.rsi_period = int(config["strategies"]["rsi_mean_reversion"]["rsi_period"])
        self.oversold = float(config["strategies"]["rsi_mean_reversion"]["oversold"])
        self.overbought = float(config["strategies"]["rsi_mean_reversion"]["overbought"])

    @staticmethod
    def _rsi(series: pd.Series, period: int) -> pd.Series:
        delta = series.diff()
        gain = (delta.clip(lower=0)).ewm(alpha=1 / period, adjust=False).mean()
        loss = (-delta.clip(upper=0)).ewm(alpha=1 / period, adjust=False).mean()
        rs = gain / (loss.replace(0, np.nan))
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50)

    def evaluate(self, symbol: str, candles: pd.DataFrame) -> List[Signal]:
        df = candles.copy()
        if len(df) < self.rsi_period + 2:
            return []
        df["rsi"] = self._rsi(df["Close"], self.rsi_period)
        last = df.iloc[-1]
        ts = df.index[-1]
        price = float(last["Close"]) if "Close" in df.columns else None
        signals: List[Signal] = []
        if last["rsi"] <= self.oversold:
            signals.append(Signal(symbol, "buy", "rsi_oversold", price, ts))
        elif last["rsi"] >= self.overbought:
            signals.append(Signal(symbol, "sell", "rsi_overbought", price, ts))
        return signals


class StrategyRegistry:
    @staticmethod
    def load_active_strategies(config: Dict) -> List[Strategy]:
        strategies: List[Strategy] = []
        for name in config["strategies"]["active"]:
            if name == "ema_crossover":
                strategies.append(EmaCrossoverStrategy(config))
            elif name == "rsi_mean_reversion":
                strategies.append(RsiMeanReversionStrategy(config))
            else:
                logger.warning("Unknown strategy in config: %s", name)
        return strategies