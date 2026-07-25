"""
Historical data loading for the backtest engine.

For now this reads OHLCV data from CSV. A `load_from_angel_one` stub is
included for the later live-integration phase -- it is NOT implemented here
because it requires your Angel One SmartAPI credentials (api_key, client
code, TOTP secret) which only you should hold, typically via a .env file
that is never committed to source control.

Expected CSV columns (case-insensitive, order doesn't matter):
    datetime, open, high, low, close, volume
"""

from pathlib import Path

import pandas as pd


def load_from_csv(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]

    required = {"datetime", "open", "high", "low", "close", "volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV is missing required columns: {missing}")

    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.sort_values("datetime").reset_index(drop=True)
    df = df.set_index("datetime")
    return df[["open", "high", "low", "close", "volume"]]


def load_from_angel_one(symbol: str, from_date: str, to_date: str, interval: str = "FIVE_MINUTE"):
    """
    Stub for Phase 3 (live/broker integration).

    Angel One SmartAPI's getCandleData endpoint needs an authenticated
    SmartConnect session (api_key + generated access token via TOTP login).
    Implementing this requires your credentials, so it's intentionally left
    for the live-integration phase rather than hardcoded here.

    Expected real implementation:
        from SmartApi import SmartConnect
        obj = SmartConnect(api_key=...)
        obj.generateSession(client_code, password, totp)
        data = obj.getCandleData({...})
        -> convert to the same DataFrame shape as load_from_csv()
    """
    raise NotImplementedError(
        "Live data fetch requires your Angel One API credentials. "
        "Use load_from_csv() for backtesting, or wire this up in Phase 3."
    )
