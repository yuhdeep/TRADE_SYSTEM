"""
Technical indicators used by the strategy engine.

All functions take/return pandas Series or add columns to a DataFrame that
has at minimum: open, high, low, close, volume (lowercase column names).
No external TA library is required -- everything is plain pandas/numpy so
the engine has zero fragile dependencies.
"""

import numpy as np
import pandas as pd


def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(period).mean()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    out = 100 - (100 / (1 + rs))
    out = out.fillna(50)  # neutral before enough data / when avg_loss == 0
    return out


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high, low, close = df["high"], df["low"], df["close"]
    prev_close = close.shift(1)
    tr = pd.concat(
        [
            (high - low),
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()


def rolling_swing_high(df: pd.DataFrame, lookback: int) -> pd.Series:
    """Highest high of the *prior* `lookback` bars (excludes current bar)."""
    return df["high"].shift(1).rolling(lookback).max()


def rolling_swing_low(df: pd.DataFrame, lookback: int) -> pd.Series:
    """Lowest low of the *prior* `lookback` bars (excludes current bar)."""
    return df["low"].shift(1).rolling(lookback).min()


def avg_volume(df: pd.DataFrame, lookback: int) -> pd.Series:
    return df["volume"].shift(1).rolling(lookback).mean()


def add_all_indicators(df: pd.DataFrame, cfg) -> pd.DataFrame:
    """Attach every indicator the strategy needs as new columns."""
    out = df.copy()
    out["ema_fast"] = ema(out["close"], cfg.EMA_FAST)
    out["ema_slow"] = ema(out["close"], cfg.EMA_SLOW)
    out["rsi"] = rsi(out["close"], cfg.RSI_PERIOD)
    out["atr"] = atr(out, cfg.ATR_PERIOD)
    out["swing_high"] = rolling_swing_high(out, cfg.SWING_LOOKBACK)
    out["swing_low"] = rolling_swing_low(out, cfg.SWING_LOOKBACK)
    out["avg_volume"] = avg_volume(out, cfg.VOLUME_LOOKBACK)
    return out
