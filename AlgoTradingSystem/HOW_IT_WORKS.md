# How This Program Works — Step by Step

This explains the whole system end to end: what each file does, and the
exact sequence of steps that happen when you run a backtest.

---

## 1. The big picture

```
Historical price data (CSV)
        │
        ▼
  Indicators (EMA, RSI, ATR, swing high/low, avg volume)
        │
        ▼
  Strategy rules (CE / PE / no signal)
        │
        ▼
  Risk management (position size, daily limits)
        │
        ▼
  Trade simulation (entry, stop-loss, target, trailing stop, exit)
        │
        ▼
  Brokerage & cost deduction
        │
        ▼
  Trade log + equity curve (CSV files)
        │
        ▼
  Dashboard (visualizes everything above)
```

Every box above is a real file in the project. Nothing is hidden — you can
open any of these and read exactly what it does.

---

## 2. File-by-file

| File | Job |
|---|---|
| `config.py` | Every tunable number in the system lives here: EMA periods, RSI thresholds, risk %, trading window, brokerage settings. Change strategy behavior by editing this file, not the logic files. |
| `data/historical.py` | Loads your OHLCV CSV into a pandas DataFrame. Also has a stub for pulling live/historical data from Angel One once you're ready for Phase 3. |
| `data/indicators.py` | Pure-math functions: EMA, RSI, ATR, rolling swing high/low, average volume. No strategy logic here — just calculations. |
| `strategy/ema_breakout_strategy.py` | The actual trading rules. Given one bar of data (with indicators already attached), decides "CE", "PE", or nothing. Also calculates the stop-loss and target for a new trade. |
| `backtest/engine.py` | The simulator. Walks through the data one candle at a time, in order, and behaves like a real trader would — it never "peeks" at future candles. |
| `backtest/costs.py` | Models what Angel One actually charges: Rs 20 per order (buy leg + sell leg = Rs 40 round trip), plus optional exchange/GST/stamp duty charges. |
| `backtest/reports.py` | Turns the list of trades into readable statistics: win rate, profit factor, drawdown, etc. |
| `run_backtest.py` | The script you actually run. Wires everything above together and writes out `backtest_trades.csv` and `equity_curve.csv`. |
| `sample_data/generate_sample_data.py` | Creates fake random-walk price data so you can test the system before you have real data. **Not real market data.** |
| `dashboard/streamlit_app.py` | Reads the CSV outputs and displays them as an interactive dashboard in your browser. |
| `broker/angel_one.py` | Empty skeleton for Phase 3 (live trading). Not used yet. |

---

## 3. What happens, step by step, when you run `python run_backtest.py`

**Step 1 — Load data**
`data/historical.py` reads your CSV, checks it has `datetime, open, high, low, close, volume`, sorts it by time, and returns a clean DataFrame.

**Step 2 — Calculate indicators**
`data/indicators.py` adds new columns to every row: `ema_fast` (20-period), `ema_slow` (50-period), `rsi`, `atr`, `swing_high`, `swing_low`, `avg_volume`. The first ~50 rows will have blank (NaN) indicators simply because there isn't enough history yet — this is normal and those rows are skipped.

**Step 3 — Walk through the data candle by candle**
The engine (`backtest/engine.py`) loops through every 5-minute candle in order:

1. **Is a trade currently open?**
   - If yes: check whether this candle's high/low hit the stop-loss or target. If trailing stop is enabled and the trade is in profit, move the stop up (for CE) or down (for PE). If it's past market close time, force-exit at the closing price.
   - If a trade closes here, record it, add the profit/loss (minus brokerage) to capital, and update the day's win/loss streak.

2. **Is a new trade allowed right now?**
   Before even checking for a signal, the engine checks:
   - Have we already hit the max trades for today? (default: 3)
   - Have we had 2 losses in a row today? (default: stop for the day)
   - Has today's loss already hit the daily loss limit? (default: 3% of capital)

   If any of these trip, no new trade is taken — even if the strategy would otherwise signal one. This is the "don't dig a deeper hole" rule.

3. **Does the strategy signal a trade?**
   `strategy/ema_breakout_strategy.py` checks, for this exact candle:
   - EMA20 vs EMA50 (trend direction)
   - RSI above/below threshold (momentum)
   - Price breaking the prior swing high/low (breakout confirmation)
   - Volume above its recent average (participation confirmation)
   - Current time inside the trading window (9:30–14:45 by default)

   All conditions must be true together, or there's no trade.

4. **If there's a signal, size the position.**
   The engine calculates: *"How many lots can I buy while risking only 1% of my capital if the stop-loss gets hit?"* It rounds down to whole lots (you can't buy half a lot). If even one lot would risk more than the allowed %, **no trade is taken** — this is why the default starting capital is Rs 5,00,000, not less: with a real 75-lot size, smaller capital often can't afford even one lot within a 1% risk budget.

**Step 4 — Repeat step 3 for every candle until the data runs out.**

**Step 5 — Force-close anything still open** at the very last candle (so no trade is left dangling).

**Step 6 — Write the results.**
Every completed trade (entry, exit, reason, cost, P&L) is written to `backtest_trades.csv`. The capital at every single candle is written to `equity_curve.csv` (used to draw the equity curve chart).

**Step 7 — Print a summary** to the terminal: total trades, win rate, profit factor, max drawdown, final capital.

---

## 4. Brokerage & costs (why every trade shows a Rs 40 cost)

Angel One charges a flat **Rs 20 per executed order**, and every completed
trade has two orders — one to enter (buy), one to exit (sell). So every
round-trip trade costs **Rs 40 in pure brokerage**, which is exactly what
you see in the `cost` column of `backtest_trades.csv`.

On top of brokerage, real trading also involves exchange transaction
charges, GST, and stamp duty — these are implemented in `backtest/costs.py`
but switched **off** by default (`INCLUDE_STATUTORY_CHARGES = False` in
`config.py`) because they're percentage-based and this backtest works on
underlying points, not actual option premium, so a percentage of "points"
isn't a meaningful number yet. Once you're backtesting against real option
premium data, flip that flag on for a fully realistic cost estimate.

---

## 5. What the dashboard shows

Run `streamlit run dashboard/app.py`. It's one control panel with five tabs:

- **📂 Data** — upload a real historical CSV, or generate synthetic test
  data, right from the browser. Preview any dataset before backtesting it.
- **⚙️ Strategy Settings** — every tunable number (EMA periods, RSI
  thresholds, risk %, daily limits, trailing stop, capital, lot size) as an
  editable form. Saving writes `settings.json`, which every backtest run
  from the dashboard uses instead of `config.py`'s hardcoded defaults.
- **▶️ Run Backtest** — pick a dataset, click run, see the headline numbers
  immediately (win rate, net P&L, profit factor, drawdown).
- **📊 Performance** — the full picture: equity curve, daily P&L, win/loss
  pie, exit-reason breakdown, and a filterable/downloadable trade log.
- **🔴 Live Monitor** — placeholder until Phase 3. Will show today's live
  position and the same daily risk tracker used in backtesting, live.

Command-line usage (`python run_backtest.py`) still works exactly as
before and is unaffected by dashboard settings — it always uses
`config.py`'s defaults unless you edit that file directly.

---

## 6. What's *not* built yet (and why)

- **Live order placement (Angel One)**: needs your real API credentials, and is the highest-stakes part of the system — one bug here places a real order. We'll build it carefully, module by module, after you've validated the strategy on real historical data.
- **Real option premium backtesting**: current engine works on the underlying's points. Real CE/PE P&L depends on premium, implied volatility, and time decay, which move differently.
- **Telegram alerts, trade journal notes, parameter optimization**: later phases per the original roadmap.

---

## 7. A note on expectations

The included sample data is a random walk — it exists only to prove the
code runs, not to demonstrate a trading edge. Any "35% return" you see on
it is meaningless. Backtest results on random data, real data, or anything
else never guarantee future performance, and a strategy that looks
profitable in backtesting can still lose money live (spreads, slippage,
and premium decay all bite harder in reality than in a simulation). Treat
this system as a tool for testing and refining a strategy carefully, not as
a guarantee of profit.
