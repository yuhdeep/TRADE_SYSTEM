"""
Auto-download real historical data from NSE, via the open-source `openchart`
library (unofficial, uses NSE's public charting API, no login required).

IMPORTANT — read before relying on this:
- This is NOT an official NSE API. It can break, get rate-limited, or
  change without notice, since it isn't a documented/supported endpoint.
- Index data (segment="IDX", e.g. NIFTY 50 itself) comes back with
  Volume = 0 for every row -- indices aren't traded, only contracts on
  them are. If you fetch index data, the strategy's volume-confirmation
  filter will never pass unless you turn REQUIRE_VOLUME_CONFIRMATION off
  in Strategy Settings.
- Equity (segment="EQ") and Futures (segment="FO") data DOES include real
  traded volume.
- Running this from a hosted server (e.g. Streamlit Community Cloud) may
  be less reliable than running it locally, since NSE can rate-limit or
  block data-center IP ranges. If cloud fetches fail, try running the
  dashboard locally instead for this step.
"""

from datetime import datetime

import pandas as pd

try:
    from openchart import NSEData
    OPENCHART_AVAILABLE = True
except ImportError:
    OPENCHART_AVAILABLE = False

SEGMENTS = {"Index": "IDX", "Equity": "EQ", "Futures": "FO"}
INTERVALS = ["1m", "5m", "10m", "15m", "30m", "1h", "1d"]


def search_symbols(query: str, segment_label: str) -> pd.DataFrame:
    """Look up valid NSE symbols matching a query, for a given segment."""
    if not OPENCHART_AVAILABLE:
        raise RuntimeError("openchart isn't installed. Run: pip install openchart")
    nse = NSEData()
    return nse.search(query, SEGMENTS[segment_label])


def fetch_historical(
    symbol: str,
    segment_label: str,
    start: datetime,
    end: datetime,
    interval: str,
) -> pd.DataFrame:
    """
    Fetch real historical OHLCV data from NSE and reshape it to match the
    exact format load_from_csv() expects: lowercase columns
    (open, high, low, close, volume), datetime index, sorted ascending.
    """
    if not OPENCHART_AVAILABLE:
        raise RuntimeError("openchart isn't installed. Run: pip install openchart")

    nse = NSEData()
    raw = nse.historical(symbol, SEGMENTS[segment_label], start, end, interval)

    if raw is None or raw.empty:
        raise ValueError(
            f"No data returned for {symbol} ({segment_label}, {interval}) "
            f"between {start.date()} and {end.date()}. Try a different date "
            f"range, symbol, or interval."
        )

    df = raw.copy()
    df.columns = [c.strip().lower() for c in df.columns]
    df.index.name = "datetime"
    df = df.sort_index()

    required = {"open", "high", "low", "close", "volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Unexpected response shape from NSE, missing columns: {missing}")

    return df[["open", "high", "low", "close", "volume"]]


def volume_is_all_zero(df: pd.DataFrame) -> bool:
    """Index data commonly comes back with zero volume on every row."""
    return (df["volume"] == 0).all()
