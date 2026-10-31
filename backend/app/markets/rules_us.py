"""United States equity trading and backtesting rules.

These rules are intentionally conservative and provider-neutral. A future
broker integration or market-data provider can override fee assumptions,
but the market semantics should remain here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


SETTLEMENT_RULE: Final = "T+1"
CURRENCY: Final = "USD"

SUPPORTS_FRACTIONAL_SHARES: Final = True
SUPPORTS_SHORT_SELLING: Final = True
HAS_PRICE_LIMIT: Final = False
HAS_AUCTION_CALL: Final = False

REGULAR_SESSION_START: Final = "09:30"
REGULAR_SESSION_END: Final = "16:00"
PREMARKET_START: Final = "04:00"
AFTERHOURS_END: Final = "20:00"


@dataclass(frozen=True)
class UsFeeModel:
    """Baseline US equity fee model.

    Values are expressed in USD. Commission is charged per order; regulatory
    fees are approximated per share and should be refined by the selected
    broker or execution venue.
    """

    commission_per_order: float = 0.0
    min_commission_per_order: float = 0.0
    sec_fee_per_share: float = 0.0000278
    taf_fee_per_share: float = 0.000166
    slippage_bps: float = 2.0

    def estimate_buy_cost(self, shares: float, price: float) -> float:
        """Estimate total cash required to buy shares at a given price."""
        if shares <= 0 or price <= 0:
            return 0.0

        notional = shares * price
        commission = max(
            self.commission_per_order,
            self.min_commission_per_order,
        )
        regulatory_fees = 0.0  # SEC/TAF fees generally apply to sales.
        slippage = notional * self.slippage_bps / 10_000
        return notional + commission + regulatory_fees + slippage

    def estimate_sell_proceeds(self, shares: float, price: float) -> float:
        """Estimate cash received after selling shares at a given price."""
        if shares <= 0 or price <= 0:
            return 0.0

        notional = shares * price
        commission = max(
            self.commission_per_order,
            self.min_commission_per_order,
        )
        regulatory_fees = shares * (self.sec_fee_per_share + self.taf_fee_per_share)
        slippage = notional * self.slippage_bps / 10_000
        return max(0.0, notional - commission - regulatory_fees - slippage)


def can_trade_in_session(session: str) -> bool:
    """Return whether orders are generally allowed in a US session."""
    return session in {"premarket", "regular", "afterhours"}


def is_price_limit_hit(*args: object) -> bool:
    """US equities do not use A-share-style daily price limits.

    Keep this helper for compatibility with CN-oriented strategy code, but it
    always returns False for the US market.
    """
    return False


def normalize_order_shares(shares: float) -> float:
    """Normalize an order quantity for US equities.

    Fractional shares are allowed by this baseline rule set. Broker-specific
    minimums should be enforced by the execution adapter.
    """
    if shares <= 0:
        raise ValueError("Order shares must be positive")
    return round(shares, 6)
