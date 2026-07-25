"""
Control panel: manage data, edit strategy settings, run backtests, and watch
results -- all from one dashboard, no editing Python files by hand.

Run:
    streamlit run dashboard/app.py
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

import settings_store
from auth import check_auth, logout_button
from data.historical import load_from_csv
from data import live_fetch
from backtest.engine import BacktestEngine
from backtest.reports import summarize
from sample_data.generate_sample_data import generate as generate_sample
import playbook_content as pb

st.set_page_config(page_title="Algo Trading Control Panel", layout="wide", page_icon="📈")

if not check_auth():
    st.stop()

DATA_DIR = ROOT / "data_files"
DATA_DIR.mkdir(exist_ok=True)
TRADES_CSV = ROOT / "backtest_trades.csv"
EQUITY_CSV = ROOT / "equity_curve.csv"

st.title("📈 Indian Algo Trading — Control Panel")
logout_button()

if "selected_data" not in st.session_state:
    st.session_state.selected_data = None

tab_data, tab_settings, tab_run, tab_perf, tab_live, tab_playbook = st.tabs(
    ["📂 Data", "⚙️ Strategy Settings", "▶️ Run Backtest", "📊 Performance", "🔴 Live Monitor", "📚 Playbook"]
)

# =============================================================================
# TAB 1 -- Data management
# =============================================================================
with tab_data:
    st.subheader("Historical data files")
    st.caption("Upload real NIFTY OHLCV CSVs here, or generate synthetic data to test the system. "
               "Required columns: `datetime, open, high, low, close, volume`.")

    col_up, col_gen = st.columns(2)
    with col_up:
        uploaded = st.file_uploader("Upload a CSV", type=["csv"])
        if uploaded is not None:
            dest = DATA_DIR / uploaded.name
            dest.write_bytes(uploaded.getvalue())
            st.success(f"Saved to data_files/{uploaded.name}")

    with col_gen:
        st.write("No real data yet? Generate a synthetic sample:")
        n_days = st.number_input("Days of 5-min data", min_value=5, max_value=250, value=20)
        if st.button("Generate sample data"):
            df = generate_sample(days=int(n_days))
            out_path = DATA_DIR / f"synthetic_{int(n_days)}d.csv"
            df.to_csv(out_path, index=False)
            st.success(f"Generated data_files/{out_path.name} ({len(df)} bars). "
                       f"Remember: this is random-walk data, not real market data.")

    st.divider()

    st.subheader("🌐 Auto-download real data from NSE")
    st.caption(
        "Pulls real historical OHLCV data directly from NSE's public charting "
        "API via the open-source `openchart` library — no login or API key "
        "needed. This is an **unofficial** data source, not an official NSE "
        "product: it can be slower, rate-limited, or occasionally unavailable, "
        "and is meant for research/backtesting, not production trading."
    )

    if not live_fetch.OPENCHART_AVAILABLE:
        st.warning(
            "The `openchart` package isn't installed. Add `openchart` to "
            "requirements.txt and reinstall (`pip install -r requirements.txt`) "
            "to enable this."
        )
    else:
        fc1, fc2, fc3 = st.columns([2, 1, 1])
        with fc1:
            symbol_query = st.text_input("Symbol (e.g. NIFTY 50, RELIANCE, NIFTY26JANFUT)", "NIFTY 50")
        with fc2:
            segment_label = st.selectbox("Segment", list(live_fetch.SEGMENTS.keys()), index=0)
        with fc3:
            interval = st.selectbox("Interval", live_fetch.INTERVALS, index=1)  # default 5m

        if segment_label == "Index":
            st.caption(
                "⚠️ Index data (NIFTY 50 itself) has **no real trading volume** "
                "(it always comes back as 0). If you use this, turn OFF "
                "'Require volume confirmation' in ⚙️ Strategy Settings, or the "
                "strategy will never fire a signal. For real volume, use "
                "'Equity' (a stock) or 'Futures' (a NIFTY futures contract) instead."
            )

        fd1, fd2 = st.columns(2)
        with fd1:
            days_back = st.slider("How many days of history", 1, 90, 20,
                                   help="Intraday data (1m/5m/etc.) is usually only available "
                                        "for a limited recent window on NSE's servers.")
        with fd2:
            st.write("")
            st.write(f"Range: last {days_back} days, ending today")

        if st.button("🔎 Search matching symbols"):
            try:
                results = live_fetch.search_symbols(symbol_query, segment_label)
                st.dataframe(results, use_container_width=True)
            except Exception as e:
                st.error(f"Search failed: {e}")

        if st.button("⬇ Download from NSE", type="primary"):
            with st.spinner(f"Fetching {symbol_query} ({segment_label}, {interval}) from NSE..."):
                try:
                    end = datetime.now()
                    start = end - timedelta(days=days_back)
                    fetched = live_fetch.fetch_historical(symbol_query, segment_label, start, end, interval)

                    safe_name = symbol_query.replace(" ", "_").replace("/", "-")
                    out_path = DATA_DIR / f"nse_{safe_name}_{interval}_{days_back}d.csv"
                    fetched.to_csv(out_path)
                    st.session_state.selected_data = out_path.name

                    if live_fetch.volume_is_all_zero(fetched):
                        st.warning(
                            f"Downloaded {len(fetched)} real bars to data_files/{out_path.name} — "
                            "but volume is 0 for every row (expected for index data). Turn OFF "
                            "'Require volume confirmation' in ⚙️ Strategy Settings before backtesting this."
                        )
                    else:
                        st.success(f"Downloaded {len(fetched)} real bars to data_files/{out_path.name}.")
                except Exception as e:
                    st.error(
                        f"Download failed: {e}\n\n"
                        "This can happen if NSE's servers are rate-limiting requests, the "
                        "symbol name doesn't match exactly (try 'Search matching symbols' "
                        "above first), or the requested date range/interval combination "
                        "isn't available. Try again, or try running the dashboard locally "
                        "instead of on the hosted version."
                    )

    st.divider()

    files = sorted(DATA_DIR.glob("*.csv"))
    if not files:
        st.info("No data files yet. Upload one or generate a sample above.")
    else:
        names = [f.name for f in files]
        default_idx = names.index(st.session_state.selected_data) if st.session_state.selected_data in names else 0
        chosen = st.selectbox("Select the active dataset (used in the Run Backtest tab)", names, index=default_idx)
        st.session_state.selected_data = chosen

        chosen_path = DATA_DIR / chosen
        try:
            preview_df = load_from_csv(chosen_path)
            c1, c2, c3 = st.columns(3)
            c1.metric("Rows", f"{len(preview_df):,}")
            c2.metric("From", str(preview_df.index.min()))
            c3.metric("To", str(preview_df.index.max()))

            fig = go.Figure(go.Scatter(x=preview_df.index, y=preview_df["close"], mode="lines",
                                        line=dict(color="#2563eb", width=1)))
            fig.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10), title="Close price preview")
            st.plotly_chart(fig, use_container_width=True)

            st.dataframe(preview_df.tail(20), use_container_width=True)

            if st.button(f"🗑 Delete {chosen}"):
                chosen_path.unlink()
                st.session_state.selected_data = None
                st.rerun()
        except Exception as e:
            st.error(f"Couldn't read {chosen}: {e}")

# =============================================================================
# TAB 2 -- Strategy settings
# =============================================================================
with tab_settings:
    st.subheader("Strategy & risk settings")
    st.caption("These override config.py defaults and are used by every backtest you run from this dashboard.")

    values = settings_store.load_settings()

    with st.form("settings_form"):
        st.markdown("**Timeframe & trading window**")
        c1, c2, c3 = st.columns(3)
        values["TIMEFRAME_MINUTES"] = c1.number_input("Candle size (minutes)", 1, 60, values["TIMEFRAME_MINUTES"])
        values["TRADING_START"] = c2.text_input("Trading start (HH:MM)", values["TRADING_START"])
        values["TRADING_END"] = c3.text_input("Trading end (HH:MM)", values["TRADING_END"])

        st.markdown("**Indicators**")
        c1, c2, c3, c4 = st.columns(4)
        values["EMA_FAST"] = c1.number_input("EMA fast", 2, 100, values["EMA_FAST"])
        values["EMA_SLOW"] = c2.number_input("EMA slow", 2, 200, values["EMA_SLOW"])
        values["RSI_PERIOD"] = c3.number_input("RSI period", 2, 50, values["RSI_PERIOD"])
        values["ATR_PERIOD"] = c4.number_input("ATR period", 2, 50, values["ATR_PERIOD"])

        c1, c2, c3 = st.columns(3)
        values["RSI_BUY_THRESHOLD"] = c1.slider("RSI buy threshold (CE)", 50, 90, values["RSI_BUY_THRESHOLD"])
        values["RSI_SELL_THRESHOLD"] = c2.slider("RSI sell threshold (PE)", 10, 50, values["RSI_SELL_THRESHOLD"])
        values["SWING_LOOKBACK"] = c3.number_input("Swing high/low lookback (bars)", 3, 50, values["SWING_LOOKBACK"])
        c1, c2 = st.columns(2)
        values["VOLUME_LOOKBACK"] = c1.number_input("Average volume lookback (bars)", 3, 100, values["VOLUME_LOOKBACK"])
        values["REQUIRE_VOLUME_CONFIRMATION"] = c2.checkbox(
            "Require volume confirmation",
            values.get("REQUIRE_VOLUME_CONFIRMATION", True),
            help="Turn OFF if your dataset has no real volume (e.g. NSE index data, "
                 "which always reports volume = 0). Leave ON for equity/futures data.",
        )

        st.markdown("**Capital & position sizing**")
        c1, c2, c3 = st.columns(3)
        values["STARTING_CAPITAL"] = c1.number_input("Starting capital (₹)", 10_000.0, 100_000_000.0,
                                                       float(values["STARTING_CAPITAL"]), step=10_000.0)
        values["LOT_SIZE"] = c2.number_input("Lot size", 1, 10_000, values["LOT_SIZE"])
        values["RISK_PER_TRADE_PCT"] = c3.slider("Risk per trade (%)", 0.1, 5.0, float(values["RISK_PER_TRADE_PCT"]), 0.1)

        st.markdown("**Exit rules**")
        c1, c2 = st.columns(2)
        values["REWARD_RISK_RATIO"] = c1.slider("Reward:Risk ratio", 1.0, 5.0, float(values["REWARD_RISK_RATIO"]), 0.5)
        values["TRAILING_SL_ENABLED"] = c2.checkbox("Trailing stop-loss enabled", values["TRAILING_SL_ENABLED"])
        c1, c2 = st.columns(2)
        values["TRAILING_SL_TRIGGER_R"] = c1.slider("Trailing SL trigger (R)", 0.5, 3.0, float(values["TRAILING_SL_TRIGGER_R"]), 0.1)
        values["TRAILING_SL_STEP_R"] = c2.slider("Trailing SL step (R)", 0.1, 2.0, float(values["TRAILING_SL_STEP_R"]), 0.1)

        st.markdown("**Daily risk limits**")
        c1, c2, c3 = st.columns(3)
        values["MAX_TRADES_PER_DAY"] = c1.number_input("Max trades/day", 1, 20, values["MAX_TRADES_PER_DAY"])
        values["MAX_CONSECUTIVE_LOSSES"] = c2.number_input("Stop after N consecutive losses", 1, 10,
                                                             values["MAX_CONSECUTIVE_LOSSES"])
        values["DAILY_LOSS_LIMIT_PCT"] = c3.slider("Daily loss limit (%)", 0.5, 10.0, float(values["DAILY_LOSS_LIMIT_PCT"]), 0.5)

        st.markdown("**Costs**")
        c1, c2 = st.columns(2)
        values["SLIPPAGE_POINTS"] = c1.number_input("Assumed slippage (points)", 0.0, 10.0, float(values["SLIPPAGE_POINTS"]), 0.1)
        values["INCLUDE_STATUTORY_CHARGES"] = c2.checkbox(
            "Include exchange/GST/stamp duty on top of ₹40 brokerage",
            values["INCLUDE_STATUTORY_CHARGES"],
        )

        saved = st.form_submit_button("💾 Save settings")
        if saved:
            settings_store.save_settings(values)
            st.success("Settings saved. They'll be used the next time you run a backtest.")

    if st.button("↩️ Reset all settings to defaults"):
        settings_store.reset_to_defaults()
        st.rerun()

# =============================================================================
# TAB 3 -- Run backtest
# =============================================================================
with tab_run:
    st.subheader("Run a backtest")

    files = sorted(DATA_DIR.glob("*.csv"))
    if not files:
        st.warning("No data files yet — add one in the 📂 Data tab first.")
    else:
        names = [f.name for f in files]
        default_idx = names.index(st.session_state.selected_data) if st.session_state.selected_data in names else 0
        run_file = st.selectbox("Dataset to backtest", names, index=default_idx, key="run_file_select")

        current = settings_store.load_settings()
        st.caption(
            f"Using: EMA {current['EMA_FAST']}/{current['EMA_SLOW']}, RSI {current['RSI_PERIOD']}, "
            f"capital ₹{current['STARTING_CAPITAL']:,.0f}, risk {current['RISK_PER_TRADE_PCT']}%/trade, "
            f"lot size {current['LOT_SIZE']}. Change these in ⚙️ Strategy Settings."
        )

        if st.button("▶️ Run Backtest", type="primary"):
            with st.spinner("Running backtest..."):
                cfg = settings_store.as_config_namespace(current)
                df = load_from_csv(DATA_DIR / run_file)
                engine = BacktestEngine(df, cfg, point_value=cfg.POINT_VALUE, lot_size=cfg.LOT_SIZE)
                trades_df = engine.run()
                trades_df.to_csv(TRADES_CSV, index=False)
                engine.equity_curve_df().to_csv(EQUITY_CSV, index=False)

            if trades_df.empty:
                st.warning("No trades were generated. Try loosening thresholds in ⚙️ Strategy Settings, "
                           "or check the dataset covers your trading window.")
            else:
                stats = summarize(trades_df, cfg.STARTING_CAPITAL)
                st.success(f"Done — {stats['total_trades']} trades. Full results in the 📊 Performance tab.")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Win Rate", f"{stats['win_rate_pct']}%")
                c2.metric("Net P&L", f"₹{stats['net_pnl']:,.0f}")
                c3.metric("Profit Factor", stats["profit_factor"])
                c4.metric("Max Drawdown", f"₹{stats['max_drawdown']:,.0f}")

# =============================================================================
# TAB 4 -- Performance dashboard
# =============================================================================
with tab_perf:
    if not TRADES_CSV.exists():
        st.info("No backtest results yet — run one in the ▶️ Run Backtest tab.")
    else:
        trades = pd.read_csv(TRADES_CSV, parse_dates=["entry_time", "exit_time"])
        equity = pd.read_csv(EQUITY_CSV, parse_dates=["datetime"]) if EQUITY_CSV.exists() else None

        if trades.empty:
            st.info("Last run produced no trades.")
        else:
            trades["date"] = trades["entry_time"].dt.date
            st.sidebar.header("Performance filters")
            min_date, max_date = trades["date"].min(), trades["date"].max()
            date_range = st.sidebar.date_input("Date range", (min_date, max_date),
                                                min_value=min_date, max_value=max_date, key="perf_date")
            direction_filter = st.sidebar.multiselect("Direction", ["CE", "PE"], default=["CE", "PE"], key="perf_dir")
            result_filter = st.sidebar.radio("Result", ["All", "Wins only", "Losses only"], key="perf_result")

            filtered = trades.copy()
            if len(date_range) == 2:
                filtered = filtered[(filtered["date"] >= date_range[0]) & (filtered["date"] <= date_range[1])]
            filtered = filtered[filtered["direction"].isin(direction_filter)]
            if result_filter == "Wins only":
                filtered = filtered[filtered["pnl"] > 0]
            elif result_filter == "Losses only":
                filtered = filtered[filtered["pnl"] <= 0]

            wins = filtered[filtered["pnl"] > 0]
            losses = filtered[filtered["pnl"] <= 0]
            net_pnl = filtered["pnl"].sum()
            total_costs = filtered["cost"].sum() if "cost" in filtered.columns else 0.0
            win_rate = (len(wins) / len(filtered) * 100) if len(filtered) else 0.0
            pf = (wins["pnl"].sum() / abs(losses["pnl"].sum())) if losses["pnl"].sum() != 0 else float("inf")

            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Total Trades", len(filtered))
            c2.metric("Win Rate", f"{win_rate:.1f}%")
            c3.metric("Net P&L", f"₹{net_pnl:,.0f}")
            c4.metric("Profit Factor", f"{pf:.2f}" if pf != float("inf") else "∞")
            c5.metric("Brokerage Paid", f"₹{total_costs:,.0f}")

            st.subheader("Equity Curve")
            if equity is not None and not equity.empty:
                fig = go.Figure(go.Scatter(x=equity["datetime"], y=equity["capital"], mode="lines",
                                            line=dict(color="#2563eb", width=2)))
                fig.update_layout(height=360, margin=dict(l=10, r=10, t=10, b=10), yaxis_title="Capital (₹)")
                st.plotly_chart(fig, use_container_width=True)

            col_left, col_right = st.columns([2, 1])
            with col_left:
                st.subheader("Daily P&L")
                daily = filtered.groupby("date")["pnl"].sum().reset_index()
                colors = ["#16a34a" if v >= 0 else "#dc2626" for v in daily["pnl"]]
                fig = go.Figure(go.Bar(x=daily["date"], y=daily["pnl"], marker_color=colors))
                fig.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10), yaxis_title="P&L (₹)")
                st.plotly_chart(fig, use_container_width=True)
            with col_right:
                st.subheader("Win / Loss")
                fig = go.Figure(go.Pie(labels=["Wins", "Losses"], values=[len(wins), len(losses)],
                                        marker_colors=["#16a34a", "#dc2626"], hole=0.55))
                fig.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(fig, use_container_width=True)

            st.subheader("Trade Log")
            display_cols = ["entry_time", "direction", "entry_price", "exit_time", "exit_price",
                             "exit_reason", "qty", "cost", "pnl"]
            display_cols = [c for c in display_cols if c in filtered.columns]
            st.dataframe(filtered[display_cols].sort_values("entry_time", ascending=False),
                         use_container_width=True, height=380)
            st.download_button("⬇ Download filtered trade log", filtered[display_cols].to_csv(index=False),
                               file_name="filtered_trades.csv", mime="text/csv")

# =============================================================================
# TAB 5 -- Live monitor (placeholder for Phase 3)
# =============================================================================
with tab_live:
    st.subheader("Live trading monitor")
    st.warning(
        "Not connected yet — this needs Phase 3 (Angel One SmartAPI integration). "
        "Once that's wired up, this tab will show today's open position, live P&L, "
        "and the same daily risk-limit tracker used in backtesting (trades today, "
        "consecutive losses, daily loss limit), refreshed in real time.",
        icon="🚧",
    )
    st.caption("Preview of what this tab will show once live trading is connected:")
    demo_cols = st.columns(4)
    demo_cols[0].metric("Trades Today", "— / 3", help="Max trades/day from your settings")
    demo_cols[1].metric("Consecutive Losses", "— / 2")
    demo_cols[2].metric("Today's P&L", "₹—")
    demo_cols[3].metric("Trading Halted?", "—")

# =============================================================================
# TAB 6 -- Playbook (educational reference, not personalized advice)
# =============================================================================
with tab_playbook:
    st.subheader("📚 Trading concepts & risk-management playbook")
    st.caption(
        "Distilled from widely-discussed trading and investing approaches. "
        "This is background knowledge to help you evaluate and refine the "
        "strategy above — it is not personalized advice and doesn't "
        "guarantee any result."
    )

    st.markdown("### Risk management — the rules this engine already enforces")
    for title, body in pb.RISK_RULES:
        with st.expander(title):
            st.write(body)

    st.markdown("### Trend & momentum principles behind the EMA/RSI strategy")
    for title, body in pb.TREND_MOMENTUM:
        with st.expander(title):
            st.write(body)

    st.markdown("### How well-known traders/investors actually operate")
    st.caption("Different styles, same underlying discipline — useful context even though this system trades intraday, not long-term.")
    for title, body in pb.PHILOSOPHIES:
        with st.expander(title):
            st.write(body)

    st.info(pb.COMMON_THREAD)
    st.divider()
    st.caption(pb.DISCLAIMER)
