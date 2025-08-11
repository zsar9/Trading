"""
Data handler: provides historical data fetching and live data streaming interfaces.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional, List

import pandas as pd

try:
    import yfinance as yf
except Exception:  # pragma: no cover - optional at runtime
    yf = None


logger = logging.getLogger(__name__)


@dataclass
class HistoricalRequest:
    symbol: str
    start: Optional[datetime]
    end: Optional[datetime]
    interval: str


_TIMEFRAME_MAP = {
    "1m": "1m",
    "2m": "2m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "60m": "60m",
    "1h": "60m",
    "1d": "1d",
}


def _ensure_cache_dir(config: Dict) -> str:
    cache_dir = config["data"]["historical"]["cache_dir"]
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir


def _cache_path(cache_dir: str, symbol: str, interval: str) -> str:
    return os.path.join(cache_dir, f"{symbol.replace('/', '_')}_{interval}.parquet")


def fetch_historical(request: HistoricalRequest, config: Dict) -> pd.DataFrame:
    """Fetch historical candles, with on-disk caching. Falls back to yfinance when enabled.

    Returns columns: [Open, High, Low, Close, Volume]
    Index: DatetimeIndex (UTC)
    """
    cache_dir = _ensure_cache_dir(config)
    cache_file = _cache_path(cache_dir, request.symbol, request.interval)

    if os.path.exists(cache_file):
        try:
            df = pd.read_parquet(cache_file)
            logger.info("Loaded cached candles for %s (%s) with %d rows", request.symbol, request.interval, len(df))
            return df
        except Exception as exc:
            logger.warning("Failed reading cache %s: %s", cache_file, exc)

    provider = config["brokers"].get("fallback_data", {}).get("provider", "yfinance")
    if provider == "yfinance" and yf is not None:
        start = request.start or (datetime.utcnow() - timedelta(days=365))
        end = request.end or datetime.utcnow()
        interval = _TIMEFRAME_MAP.get(request.interval, request.interval)
        logger.info("Fetching yfinance data for %s interval=%s", request.symbol, interval)
        df = yf.download(request.symbol, start=start, end=end, interval=interval, auto_adjust=False, progress=False)
        if not isinstance(df, pd.DataFrame) or df.empty:
            raise RuntimeError(f"No data returned for {request.symbol}")
        df = df.rename(columns={c: c.capitalize() for c in df.columns})
        df = df[[c for c in ["Open", "High", "Low", "Close", "Volume"] if c in df.columns]]
        df.index = pd.to_datetime(df.index, utc=True)
        try:
            df.to_parquet(cache_file)
        except Exception as exc:
            logger.warning("Failed writing cache %s: %s", cache_file, exc)
        return df

    raise NotImplementedError("Only yfinance fallback implemented in this skeleton.")


def get_historical_data(symbols: List[str], timeframe: str, start: Optional[datetime], end: Optional[datetime], config: Dict) -> Dict[str, pd.DataFrame]:
    result: Dict[str, pd.DataFrame] = {}
    for symbol in symbols:
        req = HistoricalRequest(symbol=symbol, start=start, end=end, interval=timeframe)
        result[symbol] = fetch_historical(req, config)
    return result


def start_stream(config: Dict) -> None:
    """Start live data streaming. Placeholder that logs configuration.

    In a full implementation, this would start websocket clients for brokers or
    consolidated market data feeds and publish bars/ticks onto an internal bus.
    """
    realtime_cfg = config.get("data", {}).get("realtime", {})
    if not realtime_cfg.get("enabled", False):
        logger.info("Realtime streaming disabled in config")
        return
    logger.info(
        "Starting realtime market data stream (websockets=%s, reconnect=%ss)",
        realtime_cfg.get("websockets", True), realtime_cfg.get("reconnect_interval_secs", 5)
    )
    # TODO: Implement Alpaca/IB websocket consumers and an internal event bus
    # For now, this is a no-op that serves as a placeholder.