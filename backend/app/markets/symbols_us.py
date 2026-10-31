"""US stock symbol utilities.

Internal canonical format:
    AAPL -> AAPL.US
    BRK.B -> BRK.B.US

User-facing display format:
    AAPL.US -> AAPL
    BRK.B.US -> BRK.B
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final

from app.markets.us import normalize_us_symbol

US_SYMBOL_SUFFIX: Final = ".US"

# Letters, digits, hyphen and at most one class-sharing dot.
_US_TICKER_RE: Final = re.compile(r"^[A-Z0-9-]+(?:\.[A-Z0-9]+)?$")


@dataclass(frozen=True)
class UsSymbol:
    internal: str
    display: str
    exchange: str | None = None

    @property
    def yfinance_symbol(self) -> str:
        """Return the symbol format normally accepted by yfinance."""
        return self.display


def is_probable_us_ticker(raw_symbol: str) -> bool:
    """Return True when the input looks like a US equity ticker."""
    symbol = raw_symbol.strip().upper()
    if not symbol:
        return False

    if symbol.endswith(US_SYMBOL_SUFFIX):
        symbol = symbol[: -len(US_SYMBOL_SUFFIX)]

    return bool(_US_TICKER_RE.match(symbol))


def normalize_symbol(raw_symbol: str) -> str:
    """Normalize a user-entered US ticker into TSP internal format."""
    return normalize_us_symbol(raw_symbol)


def to_display_symbol(internal_symbol: str) -> str:
    """Convert an internal US symbol to its user-facing ticker."""
    symbol = internal_symbol.strip().upper()
    if symbol.endswith(US_SYMBOL_SUFFIX):
        return symbol[: -len(US_SYMBOL_SUFFIX)]
    return symbol


def make_us_symbol(
    raw_symbol: str,
    exchange: str | None = None,
) -> UsSymbol:
    """Create a validated US symbol object."""
    if not is_probable_us_ticker(raw_symbol):
        raise ValueError(f"Invalid US ticker: {raw_symbol!r}")

    internal = normalize_symbol(raw_symbol)
    display = to_display_symbol(internal)

    normalized_exchange = exchange.upper() if exchange else None
    if normalized_exchange not in {None, "NYSE", "NASDAQ", "AMEX"}:
        raise ValueError(f"Unsupported US exchange: {exchange!r}")

    return UsSymbol(
        internal=internal,
        display=display,
        exchange=normalized_exchange,
    )


def split_us_symbol(internal_symbol: str) -> tuple[str, str | None]:
    """Split an internal US symbol into base ticker and optional share class.

    Examples:
        AAPL.US -> ("AAPL", None)
        BRK.B.US -> ("BRK", "B")
    """
    display = to_display_symbol(internal_symbol)
    if "." in display:
        base, share_class = display.split(".", 1)
        return base, share_class
    return display, None
