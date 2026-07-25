"""
Loads/saves strategy settings as JSON so the dashboard can edit them without
touching config.py directly. config.py remains the source of DEFAULT values;
settings.json (created the first time you save from the dashboard) holds
your overrides and always wins.
"""

import json
from pathlib import Path
from types import SimpleNamespace

import config as _defaults

SETTINGS_PATH = Path(__file__).resolve().parent / "settings.json"

# Every setting the dashboard is allowed to view/edit. Keeping an explicit
# list (rather than dumping all of config.__dict__) avoids accidentally
# exposing Python internals like __name__.
EDITABLE_KEYS = [
    "SYMBOL", "TIMEFRAME_MINUTES", "TRADING_START", "TRADING_END", "MARKET_CLOSE",
    "EMA_FAST", "EMA_SLOW", "RSI_PERIOD", "RSI_BUY_THRESHOLD", "RSI_SELL_THRESHOLD",
    "ATR_PERIOD", "VOLUME_LOOKBACK", "SWING_LOOKBACK",
    "STARTING_CAPITAL", "LOT_SIZE", "POINT_VALUE", "RISK_PER_TRADE_PCT", "REWARD_RISK_RATIO",
    "MAX_TRADES_PER_DAY", "MAX_CONSECUTIVE_LOSSES", "DAILY_LOSS_LIMIT_PCT",
    "TRAILING_SL_ENABLED", "TRAILING_SL_TRIGGER_R", "TRAILING_SL_STEP_R",
    "SLIPPAGE_POINTS", "INCLUDE_STATUTORY_CHARGES",
]


def defaults() -> dict:
    return {k: getattr(_defaults, k) for k in EDITABLE_KEYS}


def load_settings() -> dict:
    """Defaults, overridden by anything saved in settings.json."""
    values = defaults()
    if SETTINGS_PATH.exists():
        saved = json.loads(SETTINGS_PATH.read_text())
        values.update({k: v for k, v in saved.items() if k in EDITABLE_KEYS})
    return values


def save_settings(values: dict):
    SETTINGS_PATH.write_text(json.dumps(values, indent=2))


def reset_to_defaults():
    if SETTINGS_PATH.exists():
        SETTINGS_PATH.unlink()


def as_config_namespace(values: dict) -> SimpleNamespace:
    """Build an object with the same attributes as config.py, so it can be
    passed anywhere `import config` normally would be."""
    return SimpleNamespace(**values)
