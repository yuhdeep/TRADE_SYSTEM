# Indian Algo Trading System — Phase 1 + 2: Backtesting Engine & Dashboard

Backtests a NIFTY intraday EMA/RSI breakout strategy (5-minute candles)
against historical OHLCV data, with your risk rules and real Angel One
brokerage costs built in, plus a Streamlit dashboard for tracking results.

**New here?** Read `HOW_IT_WORKS.md` for a full step-by-step walkthrough of
what every file does and what happens when you run a backtest.

## Quick start (local)

```bash
pip install -r requirements.txt

# One-time: set your own login credentials (never sent anywhere, stays local)
python generate_password_hash.py
# copy the two printed lines into .streamlit/secrets.toml (see
# .streamlit/secrets.toml.example)

# Launch the control panel — manage data, edit settings, run backtests,
# and watch results, all in one place. You'll be asked to log in first.
streamlit run dashboard/app.py
```

## Deploying it as a private, hosted web app

This dashboard is gated by a username/password screen (`auth.py`) so only
someone with your credentials can use it — but a hosting platform is still
required to give it a real URL you can open from any device. Two easy, free
options:

### Option A — Streamlit Community Cloud (simplest)
1. Push this project to a **private** GitHub repo (don't commit
   `.streamlit/secrets.toml` — it's already git-ignored).
2. Go to [share.streamlit.io](https://share.streamlit.io), sign in with
   GitHub, click "New app", point it at this repo and `dashboard/app.py`.
3. In the app's **Settings → Secrets**, paste:
   ```toml
   AUTH_USERNAME = "your-username"
   AUTH_PASSWORD_HASH = "<hash from generate_password_hash.py>"
   ```
4. Deploy. You get a `https://yourapp.streamlit.app` URL — share it with no
   one, or only with people you give the password to.

### Option B — Render.com (more control, still free tier)
1. Push to GitHub (private repo recommended).
2. New "Web Service" on [render.com](https://render.com), connect the repo.
3. Build command: `pip install -r requirements.txt`
   Start command: `streamlit run dashboard/app.py --server.port $PORT --server.address 0.0.0.0`
4. Add the same `AUTH_USERNAME` / `AUTH_PASSWORD_HASH` as environment
   variables in Render's dashboard (the code checks `st.secrets` first via
   Streamlit's compatibility with env vars on non-Community-Cloud hosts —
   if needed, also add a `.streamlit/secrets.toml` written at build time
   from those env vars).

Either way: the password screen is the only thing standing between the
public internet and your dashboard, so pick a real password (not "admin123")
and don't share the URL casually.

Or drive it from the command line instead:

```bash
python sample_data/generate_sample_data.py
python run_backtest.py sample_data/nifty_5min_sample.csv
```

Your CSV needs columns: `datetime, open, high, low, close, volume`.

## The dashboard (`dashboard/app.py`)

One control panel, five tabs:

- **📂 Data** — upload real historical CSVs or generate synthetic test data,
  preview any dataset (price chart, row count, date range), delete old files.
- **⚙️ Strategy Settings** — every number in `config.py` (EMA periods, RSI
  thresholds, risk %, daily limits, trailing stop, capital, lot size, costs)
  editable from a form, saved to `settings.json`. No editing Python files.
- **▶️ Run Backtest** — pick a dataset, hit run, see win rate / P&L / profit
  factor / drawdown immediately.
- **📊 Performance** — equity curve, daily P&L, win/loss breakdown, exit
  reasons, filterable/downloadable trade log.
- **🔴 Live Monitor** — placeholder for Phase 3: once Angel One is connected,
  this tab shows today's live position, P&L, and the same daily risk-limit
  tracker (trades today, consecutive losses, halted?) used in backtesting.

## What's implemented (Phase 1 + 2)

- **Indicators** (`data/indicators.py`): EMA, RSI, ATR, rolling swing high/low,
  average volume — plain pandas, no fragile TA-library dependency.
- **Strategy** (`strategy/ema_breakout_strategy.py`): your CE/PE entry rules
  (EMA20 vs EMA50, RSI thresholds, swing breakout, volume confirmation,
  trading-window filter) plus stop/target calculation (swing level or ATR,
  capped, 1:2 reward:risk).
- **Backtest engine** (`backtest/engine.py`): bar-by-bar simulation with:
  - Position sizing from % risk per trade (real lot size, no fractional lots)
  - Trailing stop-loss
  - Max trades/day, max consecutive losses, daily loss limit (all from `config.py`)
  - Hard exit at market close
- **Real brokerage costs** (`backtest/costs.py`): Angel One charges Rs 20 per
  executed order — Rs 20 to buy, Rs 20 to sell, Rs 40 per round-trip trade.
  Optional exchange/GST/stamp-duty add-ons available (see `HOW_IT_WORKS.md`).
- **Reports** (`backtest/reports.py`): win rate, profit factor, max drawdown,
  net P&L, per-trade log exported to `backtest_trades.csv`.
- **Dashboard** (`dashboard/app.py`): a full control panel — manage data
  files, edit strategy/risk settings (persisted to `settings.json`), trigger
  backtests, and review results, all from the browser.

## Important caveats

- **This backtests the underlying's points, not option premiums.** Real CE/PE
  option P&L depends on premium, IV, and time decay (theta), which move
  differently from the underlying. Before live trading, either (a) backtest
  against actual historical option premium data, or (b) treat this as a
  directional-signal validator and size live option trades conservatively.
- **The sample data is a random walk** — it's there to prove the engine runs
  end-to-end, not to demonstrate a real edge. Any backtest "returns" on it
  are meaningless. Only trust results run against real NSE historical data.
- **Past performance (real or backtested) never guarantees future results.**
  A backtest that looks good can still be overfit to its historical sample.
- Default `STARTING_CAPITAL` (₹5,00,000) and lot size (75) are set so 1% risk
  can actually afford a real NIFTY lot given typical stop distances — the
  engine will correctly skip a trade rather than risk more than your % limit.

## Roadmap (not built yet)

- **Phase 3**: Angel One SmartAPI integration (`broker/angel_one.py` is a
  skeleton) — live data feed, order placement, position monitoring. This is
  the highest-stakes part of the system; we'll build it once the strategy is
  validated here, and test paper trading before any live order.
- **Phase 4**: parameter optimization / walk-forward testing.
- **Phase 5**: Telegram alerts, trade journal.

## Next step

Send me real historical NIFTY 5-minute OHLCV data (CSV, or tell me where
you'd source it — e.g. an export from your broker or a data vendor) so we
can backtest against reality instead of synthetic data. Once results hold up,
we move to Phase 3 (Angel One live integration).
