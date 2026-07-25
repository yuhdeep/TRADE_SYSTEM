"""
Indian brokerage & statutory charge model for options trades.

Angel One (like most discount brokers) charges flat Rs 20 per executed
order, or 0.03% of order turnover -- whichever is LOWER -- separately on
the buy leg and the sell leg. For a typical retail-size options trade the
flat Rs 20 is almost always the lower number, so a round trip (buy + sell)
costs Rs 20 + Rs 20 = Rs 40 in pure brokerage.

On top of brokerage, exchanges and the government levy additional charges
that every broker passes through:

    - Exchange transaction charges (NSE F&O): ~0.03503% of turnover
    - GST: 18% on (brokerage + exchange transaction charges)
    - Stamp duty: 0.003% of turnover, buy side only
    - SEBI charges: Rs 10 per crore of turnover (negligible at retail size)
    - STT (Securities Transaction Tax) on options: charged on the sell-side
      premium. Because this engine backtests underlying points rather than
      actual option premium, STT is left OFF by default -- turn it on once
      you're backtesting against real premium data, otherwise it understates
      cost on the underlying-points scale.

Set INCLUDE_STATUTORY_CHARGES = True in config.py to add all of the above
on top of brokerage. Left False, the engine uses the simple, real number
you already know: Rs 40 brokerage per round-trip trade.
"""

BROKERAGE_PER_ORDER = 20.0                 # Rs flat per executed order (Angel One)
BROKERAGE_PCT_OF_TURNOVER = 0.03 / 100     # 0.03%, whichever is LOWER

EXCHANGE_TXN_CHARGE_PCT = 0.03503 / 100
GST_PCT = 18 / 100
STAMP_DUTY_PCT = 0.003 / 100               # buy side only
SEBI_CHARGE_PCT = 10 / 1_00_00_000         # Rs 10 per crore


def _brokerage_per_order(turnover: float) -> float:
    return min(BROKERAGE_PER_ORDER, turnover * BROKERAGE_PCT_OF_TURNOVER)


def round_trip_cost(buy_turnover: float, sell_turnover: float, include_statutory: bool = False) -> float:
    """
    buy_turnover / sell_turnover = price x qty for the entry leg and exit
    leg respectively. Returns total Rs cost for the whole round-trip trade.
    """
    brokerage = _brokerage_per_order(buy_turnover) + _brokerage_per_order(sell_turnover)

    if not include_statutory:
        return round(brokerage, 2)

    exchange_charges = (buy_turnover + sell_turnover) * EXCHANGE_TXN_CHARGE_PCT
    gst = (brokerage + exchange_charges) * GST_PCT
    stamp_duty = buy_turnover * STAMP_DUTY_PCT
    sebi = (buy_turnover + sell_turnover) * SEBI_CHARGE_PCT

    return round(brokerage + exchange_charges + gst + stamp_duty + sebi, 2)
