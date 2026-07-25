"""
Central configuration for the Algo Trading System.
Edit these values to tune the strategy without touching engine code.
"""

# ---------------------------------------------------------------------------
# Instrument / timeframe
# ---------------------------------------------------------------------------
SYMBOL = "NIFTY"
TIMEFRAME_MINUTES = 5
TRADING_START = "09:30"
TRADING_END = "14:45"          # per the strategy doc: avoid last minutes before close
MARKET_CLOSE = "15:30"          # hard exit time for any open position

# ---------------------------------------------------------------------------
# Indicator settings
# ---------------------------------------------------------------------------
EMA_FAST = 20
EMA_SLOW = 50
RSI_PERIOD = 14
RSI_BUY_THRESHOLD = 60          # CE entries require RSI > this
RSI_SELL_THRESHOLD = 40         # PE entries require RSI < this
ATR_PERIOD = 14
VOLUME_LOOKBACK = 20            # bars used to compute average volume
SWING_LOOKBACK = 10             # bars used to detect prior swing high/low
REQUIRE_VOLUME_CONFIRMATION = True   # turn OFF if your data has no real volume
                                       # (e.g. NIFTY index data, where volume = 0)

# ---------------------------------------------------------------------------
# Risk management
# ---------------------------------------------------------------------------
STARTING_CAPITAL = 500_000.0
LOT_SIZE = 75                   # NIFTY lot size (change if trading BANKNIFTY, stocks, etc.)
POINT_VALUE = 1.0               # rupee value per point per unit qty (1.0 for underlying-points backtest)
RISK_PER_TRADE_PCT = 1.0        # % of capital risked per trade
REWARD_RISK_RATIO = 2.0         # target = 1:2 risk-reward
MAX_TRADES_PER_DAY = 3
MAX_CONSECUTIVE_LOSSES = 2      # stop trading for the day after this many losses in a row
DAILY_LOSS_LIMIT_PCT = 3.0      # stop trading for the day if drawdown exceeds this
TRAILING_SL_ENABLED = True
TRAILING_SL_TRIGGER_R = 1.0     # start trailing once trade is up 1R
TRAILING_SL_STEP_R = 0.5        # trail the stop by this many R as price advances

# ---------------------------------------------------------------------------
# Backtest engine
# ---------------------------------------------------------------------------
SLIPPAGE_POINTS = 0.5           # assumed slippage per entry/exit, in underlying points

# Brokerage: Angel One charges Rs 20 per executed order (buy + sell = Rs 40
# round trip). See backtest/costs.py for the exact model, including the
# optional exchange/GST/stamp-duty add-ons.
INCLUDE_STATUTORY_CHARGES = False   # True = also add exchange/GST/stamp duty on top of brokerage

# ---------------------------------------------------------------------------
# Broker (used in later live-trading phase, not required for backtesting)
# ---------------------------------------------------------------------------
BROKER = "angel_one"
