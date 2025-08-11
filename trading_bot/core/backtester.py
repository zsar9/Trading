"""
Backtester: historical simulation loop that runs strategies and simulates execution.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Dict, List

import pandas as pd

from . import data_handler, strategy as strategy_mod, risk_manager as risk_mod, order_executor as exec_mod, portfolio_manager as pf_mod

logger = logging.getLogger(__name__)


def _init_logging(config: Dict) -> None:
    level = getattr(logging, config.get("logging", {}).get("level", "INFO"))
    log_dir = config.get("logging", {}).get("log_dir", "./logs")
    try:
        # Avoid duplicate handlers if re-run in same process
        if not logging.getLogger().handlers:
            logging.basicConfig(level=level)
    except Exception:
        pass


def run(config: Dict) -> None:
    _init_logging(config)
    logger.info("Starting backtest")

    symbols: List[str] = config.get("dev", {}).get("test_symbols", ["AAPL"])
    start = datetime.utcnow() - timedelta(days=365)
    end = datetime.utcnow()
    timeframe = config.get("data", {}).get("historical", {}).get("default_resolution", "1d")

    candles_map = data_handler.get_historical_data(symbols, timeframe, start, end, config)

    portfolio = pf_mod.Portfolio(cash=float(config.get("backtest", {}).get("starting_capital", 100000)))
    executor = exec_mod.OrderExecutor(config)
    risk = risk_mod.RiskManager(config)
    strategies = strategy_mod.StrategyRegistry.load_active_strategies(config)

    trade_log: List[Dict] = []

    for symbol, df in candles_map.items():
        df = df.dropna().copy()
        for i in range(max(50, len(df))):
            if i < 50:
                continue
            window = df.iloc[: i + 1]
            price = float(window.iloc[-1]["Close"]) if "Close" in window.columns else None
            prices_now = {symbol: price} if price else {}
            equity = portfolio.equity(prices_now)

            for strat in strategies:
                signals = strat.evaluate(symbol, window)
                for sig in signals:
                    order_req = risk.approve_order(sig.symbol, sig.side, sig.price or price or 0.0, equity)
                    if not order_req:
                        continue
                    fill = executor.submit_order(order_req.symbol, order_req.side, order_req.quantity, price=order_req.price or price or 0.0, live=False)
                    portfolio.apply_fill(fill.symbol, fill.side, fill.quantity, fill.price)
                    trade_log.append({
                        "timestamp": fill.timestamp,
                        "symbol": fill.symbol,
                        "side": fill.side,
                        "quantity": fill.quantity,
                        "price": fill.price,
                        "strategy": strat.name,
                    })

    total_equity = portfolio.equity({sym: float(df.iloc[-1]["Close"]) for sym, df in candles_map.items()})
    logger.info("Backtest finished. Final equity: %.2f", total_equity)

    # Persist trade log if configured
    trade_log_file = config.get("logging", {}).get("trade_log_file")
    if trade_log_file:
        try:
            out = pd.DataFrame(trade_log)
            out.to_csv(trade_log_file, index=False)
            logger.info("Wrote trade log to %s (%d rows)", trade_log_file, len(out))
        except Exception as exc:
            logger.warning("Failed to write trade log: %s", exc)