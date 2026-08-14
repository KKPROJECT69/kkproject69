"""Market data source factory + exports."""
from __future__ import annotations

from ..config.settings import get_settings
from .base import MarketDataSource
from .cortex import CortexMarketSource
from .mock import MockMarketSource
from .novex import NovexPayoutSource
from .oanda import OandaMarketSource, normalize_oanda_instrument
from .quotex import QuotexProxySource, to_quotex_symbol
from .quotex_ws import QuotexTickStream
from .router import MarketSourceRouter, is_otc


def get_market_source(source: str | None = None) -> MarketDataSource:
    name = (source or get_settings().market_source).lower()
    if name == "mock":
        return MockMarketSource()
    return MarketSourceRouter()


__all__ = [
    "CortexMarketSource",
    "MarketDataSource",
    "MarketSourceRouter",
    "MockMarketSource",
    "NovexPayoutSource",
    "OandaMarketSource",
    "QuotexProxySource",
    "QuotexTickStream",
    "get_market_source",
    "is_otc",
    "normalize_oanda_instrument",
    "to_quotex_symbol",
]
