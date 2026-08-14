"""Market source router — route a pair to the correct live source.

Rules:
- OTC pairs (``*_otc`` / ``*-OTC``) → Quotex proxy candles + NovexAI payout.
- Non-OTC forex pairs → OANDA candles (no payout).
- On any upstream error, fall back to the deterministic mock source so the
  pipeline never hard-fails (fail-safe behaviour).
"""
from __future__ import annotations

import logging

from ..models.candle import Candle
from ..models.enums import Timeframe
from .base import MarketDataSource
from .mock import MockMarketSource
from .novex import NovexPayoutSource
from .oanda import OandaMarketSource, normalize_oanda_instrument
from .quotex import QuotexProxySource

log = logging.getLogger(__name__)


def is_otc(pair: str) -> bool:
    p = pair.lower()
    return "otc" in p


class MarketSourceRouter(MarketDataSource):
    name = "router"

    def __init__(
        self,
        quotex: QuotexProxySource | None = None,
        oanda: OandaMarketSource | None = None,
        payout: NovexPayoutSource | None = None,
        fallback: MarketDataSource | None = None,
    ) -> None:
        self.quotex = quotex or QuotexProxySource()
        self.oanda = oanda or OandaMarketSource()
        self.payout = payout or NovexPayoutSource()
        self.fallback = fallback or MockMarketSource()

    def _source_for(self, pair: str) -> MarketDataSource:
        if is_otc(pair):
            return self.quotex
        if normalize_oanda_instrument(pair):
            return self.oanda
        return self.fallback

    async def get_candles(
        self, pair: str, timeframe: Timeframe, count: int = 100
    ) -> list[Candle]:
        source = self._source_for(pair)
        try:
            candles = await source.get_candles(pair, timeframe, count)
            if candles:
                return candles
        except Exception as exc:  # noqa: BLE001
            log.warning("Source %s failed for %s (%s); using fallback", source.name, pair, exc)
        return await self.fallback.get_candles(pair, timeframe, count)

    async def get_payout(self, pair: str) -> float | None:
        if not is_otc(pair):
            return None
        return await self.payout.get_payout(pair)
