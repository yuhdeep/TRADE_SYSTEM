"""
Generates a synthetic 5-minute NIFTY-like OHLCV CSV so you can run and
sanity-check the backtest engine before plugging in real historical data.

This is NOT real market data -- it's a random-walk with intraday sessions,
purely so run_backtest.py has something to chew on out of the box.

Usage:
    python sample_data/generate_sample_data.py
"""

import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)


def generate(days: int = 20, start_price: float = 22000.0) -> pd.DataFrame:
    rows = []
    price = start_price
    date_range = pd.bdate_range("2025-01-01", periods=days)

    for day in date_range:
        session = pd.date_range(f"{day.date()} 09:15", f"{day.date()} 15:30", freq="5min")
        # mild daily drift + intraday volatility
        drift = RNG.normal(0, 0.0005)
        for ts in session:
            change_pct = RNG.normal(drift, 0.0015)
            open_p = price
            close_p = open_p * (1 + change_pct)
            high_p = max(open_p, close_p) * (1 + abs(RNG.normal(0, 0.0006)))
            low_p = min(open_p, close_p) * (1 - abs(RNG.normal(0, 0.0006)))
            volume = int(RNG.normal(50000, 15000))
            volume = max(volume, 1000)

            rows.append(
                {
                    "datetime": ts,
                    "open": round(open_p, 2),
                    "high": round(high_p, 2),
                    "low": round(low_p, 2),
                    "close": round(close_p, 2),
                    "volume": volume,
                }
            )
            price = close_p

    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = generate()
    out_path = "sample_data/nifty_5min_sample.csv"
    df.to_csv(out_path, index=False)
    print(f"Wrote {len(df)} bars to {out_path}")
