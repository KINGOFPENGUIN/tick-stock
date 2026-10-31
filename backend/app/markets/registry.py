from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional


class MarketCode(str, Enum):
    CN = "CN"
    US = "US"


@dataclass(frozen=True)
class Market:
    code: MarketCode
    name: str
    currency: str
    timezone: str
    exchange_names: tuple[str, ...]
    symbol_format: str
    supports_fractional_shares: bool
    supports_intraday_trading: bool
    has_price_limit: bool
    settlement_rule: str
    enabled: bool = True
    data_source: Optional[str] = None
    features: tuple[str, ...] = field(default_factory=tuple)


class MarketRegistry:
    _markets: Dict[MarketCode, Market] = {}

    @classmethod
    def register(cls, market: Market) -> None:
        cls._markets[market.code] = market

    @classmethod
    def get(cls, code: str | MarketCode) -> Market:
        if isinstance(code, str):
            try:
                code = MarketCode(code.upper())
            except ValueError as exc:
                raise ValueError(f"Unsupported market: {code}") from exc

        market = cls._markets.get(code)
        if market is None:
            raise ValueError(f"Market is not registered: {code}")

        if not market.enabled:
            raise ValueError(f"Market is disabled: {market.code}")

        return market

    @classmethod
    def list_enabled(cls) -> list[Market]:
        return [market for market in cls._markets.values() if market.enabled]

    @classmethod
    def is_supported(cls, code: str | MarketCode) -> bool:
        try:
            cls.get(code)
            return True
        except ValueError:
            return False


def get_market(code: str | MarketCode) -> Market:
    return MarketRegistry.get(code)


CN_MARKET = Market(
    code=MarketCode.CN,
    name="China A-share",
    currency="CNY",
    timezone="Asia/Shanghai",
    exchange_names=("SSE", "SZSE"),
    symbol_format="600519.SH",
    supports_fractional_shares=False,
    supports_intraday_trading=True,
    has_price_limit=True,
    settlement_rule="T+1",
    data_source=None,
    features=(
        "daily",
        "realtime",
        "financial",
        "limit_up",
        "concept",
        "industry",
    ),
)

US_MARKET = Market(
    code=MarketCode.US,
    name="United States stock",
    currency="USD",
    timezone="America/New_York",
    exchange_names=("NYSE", "NASDAQ", "AMEX"),
    symbol_format="AAPL.US",
    supports_fractional_shares=True,
    supports_intraday_trading=True,
    has_price_limit=False,
    settlement_rule="T+1",
    data_source=None,
    features=(
        "daily",
        "realtime",
        "financial",
        "premarket",
        "afterhours",
        "sector",
    ),
)

MarketRegistry.register(CN_MARKET)
MarketRegistry.register(US_MARKET)
