# Indian Algo Trading System — Complete User Guide

You've already got the app running at `localhost:8501`. This guide covers
everything from here on: daily use, what each tab does, how to read the
results, and what to do before you'd ever consider trusting this with real
money.

---

## 0. The one thing to remember throughout

This tool **backtests a strategy against historical data**. Nothing in it
places real trades, and nothing about it guarantees future profit — not
even a great-looking backtest. Treat every number here as "what would have
happened," never as "what will happen."

---

## 1. Starting the app (every time)

You only set up credentials once (already done). From now on, starting up
is just:

```powershell
cd path\to\AlgoTradingSystem\AlgoTradingSystem
streamlit run dashboard/app.py
```

Your browser opens to `localhost:8501`. Log in with the username/password
you chose. To stop the app, go back to the terminal and press `Ctrl+C`.

---

## 2. The six tabs, in the order you'll actually use them

### 📂 Data — get something to test against
- **Generate sample data**: pick a number of days, click **Generate sample
  data**. This creates random-walk data — good for confirming the system
  runs, meaningless for judging whether the strategy is any good.
- **Upload a CSV**: use this once you have real NIFTY 5-minute OHLCV data.
  Required columns: `datetime, open, high, low, close, volume` (any casing,
  any column order).
- Below the upload/generate boxes, a dropdown lets you pick which saved
  file is the **active dataset** — this is what the Run Backtest tab will
  use. You can preview any file's price chart and row count before running
  anything, and delete old files you no longer need.

### ⚙️ Strategy Settings — tune the rules
Every number that controls the strategy lives here, grouped into sections:

| Section | What it controls |
|---|---|
| Timeframe & trading window | Candle size, what hours of the day the strategy is allowed to enter trades |
| Indicators | EMA fast/slow periods, RSI period & thresholds, ATR period, swing/volume lookback windows |
| Capital & position sizing | Starting capital, lot size, % of capital risked per trade |
| Exit rules | Reward:risk ratio, whether trailing stop-loss is on, and how it behaves |
| Daily risk limits | Max trades/day, stop after N losses in a row, daily loss limit % |
| Costs | Slippage assumption, whether to include full statutory charges (GST, exchange fees, stamp duty) on top of the ₹40 brokerage |

Click **💾 Save settings** after changing anything — this writes to
`settings.json` and every backtest from here on uses these values instead
of the hardcoded defaults in `config.py`. Click **↩️ Reset all settings to
defaults** any time to go back to the original numbers.

**Nothing here is "correct."** These are starting points to experiment
with, not values with magical properties.

### ▶️ Run Backtest — the actual test
1. Pick which dataset to test against (from the dropdown).
2. Check the caption line — it shows a summary of the settings that will
   be used, so you can confirm before running.
3. Click **▶️ Run Backtest**.
4. You'll immediately see four headline numbers: Win Rate, Net P&L, Profit
   Factor, Max Drawdown.

If it says **"No trades were generated"**, that's not a bug — it means
your settings + data combination never produced a signal that met every
condition (EMA alignment, RSI threshold, breakout, volume, trading window,
all at once). Try loosening thresholds in ⚙️ Strategy Settings, or confirm
your data actually covers the trading window you configured.

### 📊 Performance — the full picture
This is where you actually evaluate a backtest, not just skim headline
numbers:
- **Equity Curve** — capital over time. A strategy that's profitable
  overall but has long, deep drawdowns is riskier to actually live-trade
  than the headline "net P&L" suggests.
- **Daily P&L** — bar chart, green/red. Look for whether profit is coming
  from a handful of lucky days or is broadly consistent.
- **Win/Loss pie** — win rate alone means nothing without knowing average
  win size vs. average loss size (that's what Profit Factor captures).
- **Trade Log** — every single trade, filterable by date range, direction
  (CE/PE), and win/loss. Downloadable as CSV.

**Reading the summary metrics:**

| Metric | What it means | What to watch for |
|---|---|---|
| Win Rate | % of trades that were profitable | A low win rate (even 35-40%) can still be a good system if winners are much bigger than losers |
| Profit Factor | Gross profit ÷ gross loss | Above 1.5–2 is generally considered healthy; below 1 means the system loses money overall |
| Max Drawdown | Largest peak-to-trough capital drop | This is the number that tells you what it would actually *feel* like to run this live — a 15% drawdown is a very different experience than a 3% one, even if final returns look similar |
| Net Return % | Total P&L as % of starting capital | Meaningless on its own without knowing the time period and drawdown involved |

### 🔴 Live Monitor — not active yet
This is a placeholder for Phase 3 (live broker connection via Angel One),
which isn't built. Nothing here does anything real yet — it's a preview of
what the layout will show once that phase exists.

### 📚 Playbook — reference material
Background on *why* the strategy's rules exist — position sizing, stop-loss
discipline, trend-following logic, and how well-known traders (Livermore,
O'Neil, Minervini, Jhunjhunwala, Graham/Buffett) actually operate. Good to
read once, and to revisit whenever you're tempted to override a rule
"just this once."

---

## 3. A sensible workflow for actually improving the strategy

1. Generate synthetic data, run a backtest, confirm the app works
   end-to-end. (You've done this.)
2. Get **real historical NIFTY 5-minute data** — from your broker's
   export tools, or a data vendor. Random-walk data cannot tell you
   anything about whether this strategy has an edge.
3. Upload the real data, run the backtest with default settings first.
4. Change **one setting at a time** in ⚙️ Strategy Settings, re-run, and
   compare Performance tab results. Changing many settings at once makes
   it impossible to know what actually helped.
5. Be suspicious of settings that look "too good" on one dataset — that's
   usually overfitting to that specific historical period, not a real
   edge. Test across multiple different time periods if you can.
6. Only after this — and ideally after paper-trading the signals manually
   for a while — would live trading (Phase 3, not yet built) be worth
   discussing.

---

## 4. Troubleshooting quick reference

| Problem | Likely cause | Fix |
|---|---|---|
| `No such file or directory: requirements.txt` | Terminal isn't in the folder containing the project files | `cd` into the folder that directly contains `requirements.txt` |
| `StreamlitSecretNotFoundError` | `.streamlit/secrets.toml` doesn't exist yet | Create it (copy from `secrets.toml.example`), paste your `AUTH_USERNAME`/`AUTH_PASSWORD_HASH` |
| Login rejected | Typo in username/password, or secrets.toml has the placeholder text still in it | Double check exact username you chose, and that you swapped in the real hash |
| "No trades were generated" | Settings + data never produce a qualifying signal | Loosen RSI thresholds, check your data covers the trading window (09:30–14:45 by default) |
| VS Code update popup during pip install | Unrelated background VS Code self-update, not your project | Click "Cancel installation" — pip install underneath is unaffected |

---

## 5. Hosting it so you can access it from anywhere

Covered in detail in the project's `README.md` — short version:
1. Push the project to a **private** GitHub repo (don't commit the real
   `secrets.toml` — it's already git-ignored).
2. Create a free account at [share.streamlit.io](https://share.streamlit.io),
   connect the repo, point it at `dashboard/app.py`.
3. Paste your `AUTH_USERNAME`/`AUTH_PASSWORD_HASH` into that app's
   **Settings → Secrets** panel.
4. Deploy — you get a permanent URL, gated by your login screen.

---

## 6. Standing reminders

- Backtest results, real or synthetic, never guarantee future performance.
- This system trades the underlying's points, not real option premiums —
  actual CE/PE P&L depends on premium, IV, and time decay, which behave
  differently.
- No configuration of this tool, and nothing in the Playbook tab, is
  personalized financial advice. Consider a SEBI-registered advisor before
  risking real capital.