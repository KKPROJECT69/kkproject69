"""Deterministic synthetic market source for offline development & tests."""
from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta

from ..models.candle import Candle
from ..models.enums import Timeframe
from .base import MarketDataSource


class MockMarketSource(MarketDataSource):
    name = "mock"

    def __init__(self, seed: int = 42, start_price: float = 100.0) -> None:
        self._rng = random.Random(seed)
        self._start_price = start_price

    async def get_candles(
        self, pair: str, timeframe: Timeframe, count: int = 100
    ) -> list[Candle]:
        rng = self._rng
        price = self._start_price
        step = timedelta(seconds=timeframe.seconds)
        start = datetime.now(UTC) - step * count
        candles: list[Candle] = []
        for i in range(count):
            ts = start + step * i
            open_ = price
            drift = rng.uniform(-1.5, 1.5)
            close = open_ + drift
            high = max(open_, close) + rng.uniform(0.0, 0.8)
            low = min(open_, close) - rng.uniform(0.0, 0.8)
            volume = rng.uniform(100.0, 1000.0)
            payout = round(75.0 + rng.uniform(0.0, 18.0), 1)
            candles.append(
                Candle(
                    timestamp=ts,
                    open=round(open_, 4),
                    high=round(high, 4),
                    low=round(low, 4),
                    close=round(close, 4),
                    volume=round(volume, 2),
                    payout=payout,
                    source_timezone="UTC",
                )
            )
            price = close
        return candles

    async def get_payout(self, pair: str) -> float | None:
        return round(75.0 + self._rng.uniform(0.0, 18.0), 1)
