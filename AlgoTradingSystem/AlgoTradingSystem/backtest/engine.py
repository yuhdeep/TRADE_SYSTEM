"""
Event-driven backtest engine.

Walks the OHLCV data bar by bar (no lookahead: every decision at bar t only
uses data available at bar t), applies the strategy + risk rules from
config.py, and records every trade for reporting.
"""

from dataclasses import dataclass, field

import pandas as pd

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from data.indicators import add_all_indicators
from strategy.ema_breakout_strategy import generate_signal, initial_stop_and_target
from backtest.costs import round_trip_cost


@dataclass
class Trade:
    direction: str
    entry_time: pd.Timestamp
    entry_price: float
    stop: float
    target: float
    qty: int
    exit_time: pd.Timestamp = None
    exit_price: float = None
    exit_reason: str = None
    pnl: float = 0.0
    cost: float = 0.0

    def close(self, time, price, reason, point_value: float = 1.0, cost: float = 0.0):
        self.exit_time = time
        self.exit_price = price
        self.exit_reason = reason
        direction_sign = 1 if self.direction == "CE" else -1
        self.pnl = direction_sign * (price - self.entry_price) * self.qty * point_value - cost
        self.cost = cost


@dataclass
class DayState:
    trades_today: int = 0
    consecutive_losses: int = 0
    pnl_today: float = 0.0
    trading_halted: bool = False


class BacktestEngine:
    def __init__(self, df: pd.DataFrame, cfg, point_value: float = 1.0, lot_size: int = 75):
        """
        df: raw OHLCV DataFrame (datetime index)
        cfg: config module (see config.py)
        point_value: rupee value of 1 point move per unit quantity
                     (for a direct underlying-points backtest this is 1.0;
                     if simulating option premium P&L, adjust accordingly)
        lot_size: quantity per trade (e.g. NIFTY lot size)
        """
        self.cfg = cfg
        self.point_value = point_value
        self.lot_size = lot_size
        self.df = add_all_indicators(df, cfg)
        self.capital = cfg.STARTING_CAPITAL
        self.equity_curve = []
        self.trades: list[Trade] = []
        self._open_trade: Trade | None = None
        self._day_state = DayState()
        self._current_day = None

    # ------------------------------------------------------------------
    def _reset_day_if_needed(self, ts: pd.Timestamp):
        day = ts.date()
        if day != self._current_day:
            self._current_day = day
            self._day_state = DayState()

    def _risk_amount(self) -> float:
        return self.capital * (self.cfg.RISK_PER_TRADE_PCT / 100.0)

    def _position_size(self, entry: float, stop: float) -> int:
        risk_per_unit = abs(entry - stop) * self.point_value
        if risk_per_unit <= 0:
            return 0
        raw_qty = self._risk_amount() / risk_per_unit
        # round down to whole lots
        lots = max(int(raw_qty // self.lot_size), 0)
        return lots * self.lot_size

    def _can_take_new_trade(self) -> bool:
        s = self._day_state
        if s.trading_halted:
            return False
        if s.trades_today >= self.cfg.MAX_TRADES_PER_DAY:
            return False
        if s.consecutive_losses >= self.cfg.MAX_CONSECUTIVE_LOSSES:
            return False
        if s.pnl_today <= -self.capital * (self.cfg.DAILY_LOSS_LIMIT_PCT / 100.0):
            return False
        return True

    def _apply_trailing_stop(self, trade: Trade, row: pd.Series):
        if not self.cfg.TRAILING_SL_ENABLED:
            return
        risk = abs(trade.entry_price - trade.stop)
        if risk <= 0:
            return
        direction_sign = 1 if trade.direction == "CE" else -1
        gain_r = direction_sign * (row["close"] - trade.entry_price) / risk

        if gain_r >= self.cfg.TRAILING_SL_TRIGGER_R:
            steps = int(gain_r // self.cfg.TRAILING_SL_STEP_R)
            new_stop = trade.entry_price + direction_sign * (steps * self.cfg.TRAILING_SL_STEP_R - 1) * risk
            if trade.direction == "CE":
                trade.stop = max(trade.stop, new_stop)
            else:
                trade.stop = min(trade.stop, new_stop)

    # ------------------------------------------------------------------
    def run(self) -> pd.DataFrame:
        for ts, row in self.df.iterrows():
            self._reset_day_if_needed(ts)

            if self._open_trade is not None:
                self._manage_open_trade(ts, row)

            if self._open_trade is None and self._can_take_new_trade():
                self._maybe_enter_trade(ts, row)

            self.equity_curve.append({"datetime": ts, "capital": self.capital})

        # force-close anything still open at the end of data
        if self._open_trade is not None:
            last_ts = self.df.index[-1]
            last_row = self.df.iloc[-1]
            self._exit_trade(last_ts, last_row["close"], "end_of_data")

        return self.results()

    # ------------------------------------------------------------------
    def _manage_open_trade(self, ts: pd.Timestamp, row: pd.Series):
        trade = self._open_trade
        time_str = ts.strftime("%H:%M")

        self._apply_trailing_stop(trade, row)

        if trade.direction == "CE":
            if row["low"] <= trade.stop:
                self._exit_trade(ts, trade.stop, "stop_loss")
                return
            if row["high"] >= trade.target:
                self._exit_trade(ts, trade.target, "target")
                return
        else:
            if row["high"] >= trade.stop:
                self._exit_trade(ts, trade.stop, "stop_loss")
                return
            if row["low"] <= trade.target:
                self._exit_trade(ts, trade.target, "target")
                return

        if time_str >= self.cfg.MARKET_CLOSE:
            self._exit_trade(ts, row["close"], "market_close")

    def _exit_trade(self, ts, price, reason):
        trade = self._open_trade
        buy_turnover = trade.entry_price * trade.qty
        sell_turnover = price * trade.qty
        cost = round_trip_cost(buy_turnover, sell_turnover, self.cfg.INCLUDE_STATUTORY_CHARGES)
        trade.close(ts, price, reason, self.point_value, cost)
        self.capital += trade.pnl
        self._day_state.pnl_today += trade.pnl
        if trade.pnl < 0:
            self._day_state.consecutive_losses += 1
        else:
            self._day_state.consecutive_losses = 0
        self.trades.append(trade)
        self._open_trade = None

    def _maybe_enter_trade(self, ts: pd.Timestamp, row: pd.Series):
        signal = generate_signal(row, self.cfg)
        if signal is None:
            return

        stop, target = initial_stop_and_target(row, signal, self.cfg)
        entry_price = row["close"] + (self.cfg.SLIPPAGE_POINTS if signal == "CE" else -self.cfg.SLIPPAGE_POINTS)
        qty = self._position_size(entry_price, stop)
        if qty <= 0:
            return

        self._open_trade = Trade(
            direction=signal,
            entry_time=ts,
            entry_price=entry_price,
            stop=stop,
            target=target,
            qty=qty,
        )
        self._day_state.trades_today += 1

    # ------------------------------------------------------------------
    def equity_curve_df(self) -> pd.DataFrame:
        return pd.DataFrame(self.equity_curve)

    def results(self) -> pd.DataFrame:
        rows = [
            {
                "entry_time": t.entry_time,
                "direction": t.direction,
                "entry_price": round(t.entry_price, 2),
                "exit_time": t.exit_time,
                "exit_price": round(t.exit_price, 2) if t.exit_price else None,
                "exit_reason": t.exit_reason,
                "qty": t.qty,
                "cost": round(t.cost, 2),
                "pnl": round(t.pnl, 2),
            }
            for t in self.trades
        ]
        return pd.DataFrame(rows)
