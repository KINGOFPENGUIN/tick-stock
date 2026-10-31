"""United States stock market definition."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import time
from typing import Final

from app.markets.registry import MarketCode, MarketRegistry


US_TIMEZONE: Final = "America/New_York"
US_CURRENCY: Final = "USD"

US_INDICES: Final[tuple[dict[str, str], ...]] = (
    {"symbol": "SPX.US", "name": "S&P 500", "yfinance_symbol": "^GSPC"},
    {"symbol": "NDX.US", "name": "Nasdaq 100", "yfinance_symbol": "^NDX"},
    {"symbol": "DJI.US", "name": "Dow Jones Industrial Average", "yfinance_symbol": "^DJI"},
    {"symbol": "RUT.US", "name": "Russell 2000", "yfinance_symbol": "^RUT"},
    {"symbol": "VIX.US", "name": "CBOE Volatility Index", "yfinance_symbol": "^VIX"},
)

US_SECTORS: Final[tuple[str, ...]] = (
    "Technology",
    "Communication Services",
    "Consumer Discretionary",
    "Consumer Staples",
    "Health Care",
    "Financials",
    "Industrials",
    "Energy",
    "Utilities",
    "Real Estate",
    "Materials",
)


@dataclass(frozen=True)
class UsSession:
    name: str
    start: time
    end: time


PREMARKET_SESSION: Final = UsSession(
    name="premarket",
    start=time(4, 0),
    end=time(9, 30),
)

REGULAR_SESSION: Final = UsSession(
    name="regular",
    start=time(9, 30),
    end=time(16, 0),
)

AFTERHOURS_SESSION: Final = UsSession(
    name="afterhours",
    start=time(16, 0),
    end=time(20, 0),
)

US_SESSIONS: Final[tuple[UsSession, ...]] = (
    PREMARKET_SESSION,
    REGULAR_SESSION,
    AFTERHOURS_SESSION,
)


def normalize_us_symbol(raw_symbol: str) -> str:
    """Normalize a user-entered US ticker to the internal TSP format.

    Examples:
        AAPL -> AAPL.US
        aapl.us -> AAPL.US
        BRK.B -> BRK.B.US
    """
    symbol = raw_symbol.strip().upper()
    if not symbol:
        raise ValueError("US symbol cannot be empty")

    if "." in symbol:
        base, suffix = symbol.split(".", 1)
        if suffix.upper() == "US":
            return symbol
        return f"{base}.{suffix}.US"

    return f"{symbol}.US"


def display_us_symbol(internal_symbol: str) -> str:
    """Convert an internal US symbol to a user-facing ticker.

    Example: AAPL.US -> AAPL
    """
    symbol = internal_symbol.strip().upper()
    if symbol.endswith(".US"):
        return symbol[:-3]
    return symbol


def get_us_market():
    return MarketRegistry.get(MarketCode.US)
