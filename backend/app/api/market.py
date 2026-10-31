"""Market selection API.

Provides read-only market metadata and a lightweight market switch endpoint.
The current implementation stores the selected market in process settings;
a future multi-user deployment can move this to a per-session preference.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import get_default_market, settings
from app.markets.registry import MarketRegistry

router = APIRouter(prefix="/api/market", tags=["market"])


class MarketSwitchRequest(BaseModel):
    market: str


@router.get("/current")
def current_market() -> dict:
    """Return the currently selected market."""
    market = get_default_market()
    return {
        "market": market,
        "is_us": market == "US",
        "is_cn": market == "CN",
        "us_data_source": settings.us_data_source,
    }


@router.get("/supported")
def supported_markets() -> list[dict]:
    """Return all enabled markets registered in the market layer."""
    return [
        {
            "code": market.code.value,
            "name": market.name,
            "currency": market.currency,
            "timezone": market.timezone,
            "symbol_format": market.symbol_format,
            "data_source": market.data_source,
            "features": list(market.features),
        }
        for market in MarketRegistry.list_enabled()
    ]


@router.post("/switch")
def switch_market(request: MarketSwitchRequest) -> dict:
    """Switch the process-wide default market.

    This is intentionally simple for the first US-market milestone. It does
    not yet persist the choice across backend restarts; use DEFAULT_MARKET in
    .env for a persistent deployment setting.
    """
    market = request.market.strip().upper()
    if not MarketRegistry.is_supported(market):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported market: {market}; expected CN or US",
        )

    settings.default_market = market
    return current_market()
