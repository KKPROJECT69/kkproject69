"""Market data source factory."""
from __future__ import annotations

from ..config.settings import get_settings
from .base import MarketDataSource
from .cortex import CortexMarketSource
from .mock import MockMarketSource
from .novex import NovexMarketSource
from .oanda import OandaMarketSource


def get_market_source(source: str | None = None) -> MarketDataSource:
    name = (source or get_settings().market_source).lower()
    if name == "novex":
        return NovexMarketSource()
    if name == "oanda":
        return OandaMarketSource()
    if name == "cortex":
        return CortexMarketSource()
    return MockMarketSource()


__all__ = [
    "CortexMarketSource",
    "MarketDataSource",
    "MockMarketSource",
    "NovexMarketSource",
    "OandaMarketSource",
    "get_market_source",
]
