"""
Entry point: run the backtest against a CSV of historical OHLCV data.

Usage:
    python run_backtest.py sample_data/nifty_5min_sample.csv
    python run_backtest.py path/to/your_real_data.csv
"""

import sys

import config
from data.historical import load_from_csv
from backtest.engine import BacktestEngine
from backtest.reports import print_summary


def main(csv_path: str):
    df = load_from_csv(csv_path)
    print(f"Loaded {len(df)} bars from {csv_path} "
          f"({df.index.min()} -> {df.index.max()})")

    engine = BacktestEngine(df, config, point_value=config.POINT_VALUE, lot_size=config.LOT_SIZE)
    trades_df = engine.run()

    if not trades_df.empty:
        print("\nLast 10 trades:")
        print(trades_df.tail(10).to_string(index=False))

    print_summary(trades_df, config.STARTING_CAPITAL)

    out_path = "backtest_trades.csv"
    trades_df.to_csv(out_path, index=False)
    print(f"Full trade log written to {out_path}")

    equity_path = "equity_curve.csv"
    engine.equity_curve_df().to_csv(equity_path, index=False)
    print(f"Equity curve written to {equity_path}")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "sample_data/nifty_5min_sample.csv"
    main(path)
