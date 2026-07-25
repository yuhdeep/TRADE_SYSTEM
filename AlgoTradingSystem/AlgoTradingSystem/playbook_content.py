"""
Reference content for the '📚 Playbook' dashboard tab.

Educational summaries only -- distilled from widely-known trading and
investing principles. None of this is personalized financial advice, and
none of it guarantees this system (or any system) will trade profitably.
"""

RISK_RULES = [
    ("Risk a small, fixed slice per trade",
     "Most disciplined traders cap the loss on any single trade at 1-2% of "
     "total capital. This system's `RISK_PER_TRADE_PCT` setting implements "
     "exactly this -- position size is derived from your stop distance, "
     "not picked arbitrarily."),
    ("Decide the stop-loss before you enter, never after",
     "A stop should come from chart structure (a swing level, a moving "
     "average, or a fixed % band) decided before the trade, not moved "
     "further away once a trade is underwater. This engine sets the stop "
     "at entry and only ever tightens it via the trailing-stop logic."),
    ("Cap exposure to any one setup",
     "Concentrating too much capital in one idea, however confident you "
     "are, magnifies the damage from being wrong. Daily trade caps and "
     "consecutive-loss halts in this system exist for the same reason."),
    ("Stop trading after a losing streak, not after a target",
     "Revenge trading -- trying to immediately win back a loss with a "
     "bigger, less disciplined trade -- is one of the fastest ways to blow "
     "up an account. `MAX_CONSECUTIVE_LOSSES` and `DAILY_LOSS_LIMIT_PCT` "
     "encode this as a hard rule rather than a willpower test."),
    ("Let winners run, cut losers fast",
     "Trailing stops exist so a winning trade isn't closed out at the "
     "first sign of profit while a losing trade is allowed to bleed."),
]

TREND_MOMENTUM = [
    ("Trade with the dominant trend",
     "Nearly every well-known trend/momentum trader (Livermore, O'Neil, "
     "Minervini) independently converged on this: don't fight the "
     "prevailing direction of price. This system's EMA20/EMA50 relationship "
     "is exactly this filter -- CE signals only fire when the fast EMA is "
     "above the slow EMA, and vice versa for PE."),
    ("Confirm breakouts with volume",
     "A price breakout on low volume is much more likely to fail or "
     "reverse than one backed by strong participation. The engine's "
     "avg-volume check implements this directly."),
    ("Wait for your own defined trigger, not FOMO",
     "Chasing a move that already happened, without your setup actually "
     "confirming, is one of the most common retail mistakes. A rules-based "
     "system removes the temptation, but only if you don't override it "
     "manually mid-session."),
]

PHILOSOPHIES = [
    ("Jesse Livermore — trend & patience",
     "Trade in the direction of least resistance, add to positions that "
     "are proving themselves, never add to a loser, and treat patience "
     "itself as a skill -- most of the work is waiting, not acting."),
    ("William O'Neil — CANSLIM",
     "A checklist for growth-style entries: strong current and multi-year "
     "earnings growth, a catalyst (new product/management/price high), "
     "rising volume with lower float, buying the sector leader rather than "
     "the cheapest name, rising institutional ownership, and -- critically "
     "-- trading with the broader market's direction rather than against it."),
    ("Mark Minervini — SEPA",
     "Only buy stocks in a confirmed uptrend (price above rising major "
     "moving averages, properly aligned), favor volatility-contraction "
     "patterns as low-risk entries, and cap losses at a strict 5-10% per "
     "trade with zero exceptions."),
    ("Rakesh Jhunjhunwala — high-conviction value",
     "Combined value investing with concentrated, long-horizon bets on "
     "scalable businesses run by capable management, bought at reasonable "
     "valuations relative to growth -- and treated the market's price "
     "action as information to respect, not ignore."),
    ("Graham/Buffett — margin of safety",
     "Invest in businesses you actually understand, at a meaningful "
     "discount to your estimate of intrinsic value, so valuation mistakes "
     "don't wipe you out. This is a long-horizon, low-turnover philosophy "
     "-- a different animal from this system's intraday breakout approach."),
]

COMMON_THREAD = (
    "Despite very different styles -- long-term value investing vs "
    "intraday momentum trading -- every one of the approaches above shares "
    "four things: a defined process applied consistently, strict risk "
    "control, patience to wait for a real setup instead of forcing trades, "
    "and treating losses as a routine cost of doing business rather than a "
    "personal failure. A profitable-looking backtest without those "
    "disciplines behind it is not a strategy, it's a coincidence."
)

DISCLAIMER = (
    "This is educational information distilled from widely-discussed "
    "trading and investing approaches -- it is not personalized investment "
    "advice, and no strategy or backtest result (including this system's) "
    "guarantees future profit. Trading involves real risk of capital loss. "
    "Consider consulting a SEBI-registered investment advisor for advice "
    "tailored to your situation, and verify any current tax, margin, or "
    "SEBI rules independently since these change with each Union Budget "
    "and regulatory circular."
)
