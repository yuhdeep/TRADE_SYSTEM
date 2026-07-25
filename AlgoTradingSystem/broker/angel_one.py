"""
Angel One SmartAPI integration -- SKELETON ONLY.

This phase (backtesting) doesn't need this file at all. It's here so the
project structure matches the full roadmap and so Phase 3 (live execution)
has a clear place to land.

To actually go live later you will need, in a local .env file (never
committed to git):
    ANGEL_API_KEY=...
    ANGEL_CLIENT_CODE=...
    ANGEL_PASSWORD=...
    ANGEL_TOTP_SECRET=...

Install: pip install smartapi-python pyotp

We will implement generateSession(), placeOrder(), getPosition(), and
getCandleData() together once you're ready for Phase 3 -- live order
placement is the highest-stakes part of this system and deserves careful,
incremental testing (paper trading -> tiny real size -> full size) before
any code here places a real order.
"""

import os


class AngelOneBroker:
    def __init__(self):
        self.api_key = os.getenv("ANGEL_API_KEY")
        self.client_code = os.getenv("ANGEL_CLIENT_CODE")
        self.password = os.getenv("ANGEL_PASSWORD")
        self.totp_secret = os.getenv("ANGEL_TOTP_SECRET")
        self.session = None

    def connect(self):
        raise NotImplementedError(
            "Live broker connection is built in Phase 3, once the strategy "
            "has been validated in backtesting and paper trading."
        )

    def place_order(self, symbol: str, qty: int, transaction_type: str, order_type: str = "MARKET"):
        raise NotImplementedError("Implemented in Phase 3 alongside connect().")

    def get_positions(self):
        raise NotImplementedError("Implemented in Phase 3 alongside connect().")
