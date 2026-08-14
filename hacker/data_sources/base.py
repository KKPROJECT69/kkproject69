"""Market data source interface. Keeps upstream providers isolated."""
from __future__ import annotations

from abc import ABC, abstractmethod

from ..models.candle import Candle
from ..models.enums import Timeframe


class MarketDataSource(ABC):
    name: str = "base"

    @abstractmethod
    async def get_candles(
        self, pair: str, timeframe: Timeframe, count: int = 100
    ) -> list[Candle]:
        """Return normalized candles, oldest first."""

    async def get_payout(self, pair: str) -> float | None:
        """Return current payout % for a pair when the source provides it."""
        return None
