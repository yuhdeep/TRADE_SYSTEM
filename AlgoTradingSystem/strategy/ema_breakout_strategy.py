"""
Strategy engine implementing the rules from your trading plan:

Buy CE (bullish) when:
    - EMA20 > EMA50
    - RSI > 60
    - Close breaks above the prior swing high
    - Volume > average volume
    - Time is within the trading window

Buy PE (bearish) when:
    - EMA20 < EMA50
    - RSI < 40
    - Close breaks below the prior swing low
    - Volume > average volume
    - Time is within the trading window

This module is directional-signal-only: it decides CE vs PE vs no-trade on
the underlying (NIFTY). Translating that into an actual option contract
(strike, premium) happens in the execution layer, since that needs live
option-chain data that isn't available at backtest time.
"""

from datetime import datetime

import pandas as pd


def _in_trading_window(ts: pd.Timestamp, start: str, end: str) -> bool:
    t = ts.strftime("%H:%M")
    return start <= t <= end


def generate_signal(row: pd.Series, cfg) -> str | None:
    """
    Returns "CE", "PE", or None for a single indicator-enriched bar (row).
    Any NaN indicator (not enough warm-up bars yet) yields no signal.
    """
    required = ["ema_fast", "ema_slow", "rsi", "swing_high", "swing_low", "avg_volume"]
    if row[required].isna().any():
        return None

    if not _in_trading_window(row.name, cfg.TRADING_START, cfg.TRADING_END):
        return None

    bullish = (
        row["ema_fast"] > row["ema_slow"]
        and row["rsi"] > cfg.RSI_BUY_THRESHOLD
        and row["close"] > row["swing_high"]
        and row["volume"] > row["avg_volume"]
    )
    if bullish:
        return "CE"

    bearish = (
        row["ema_fast"] < row["ema_slow"]
        and row["rsi"] < cfg.RSI_SELL_THRESHOLD
        and row["close"] < row["swing_low"]
        and row["volume"] > row["avg_volume"]
    )
    if bearish:
        return "PE"

    return None


def initial_stop_and_target(row: pd.Series, direction: str, cfg) -> tuple[float, float]:
    """
    Stop-loss at the swing high/low (fallback to ATR if the swing level is
    unreasonably far away), target at the configured reward:risk ratio.
    """
    entry = row["close"]
    atr_stop_distance = row["atr"] * 1.5

    if direction == "CE":
        swing_stop_distance = entry - row["swing_low"]
        stop_distance = min(swing_stop_distance, atr_stop_distance) if swing_stop_distance > 0 else atr_stop_distance
        stop = entry - stop_distance
        target = entry + stop_distance * cfg.REWARD_RISK_RATIO
    else:  # PE
        swing_stop_distance = row["swing_high"] - entry
        stop_distance = min(swing_stop_distance, atr_stop_distance) if swing_stop_distance > 0 else atr_stop_distance
        stop = entry + stop_distance
        target = entry - stop_distance * cfg.REWARD_RISK_RATIO

    return stop, target
