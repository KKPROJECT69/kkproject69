"""Normalized OHLC candle used everywhere downstream of the adapters."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Candle:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    payout: float | None = None
    source_timezone: str | None = None

    @property
    def is_bullish(self) -> bool:
        return self.close > self.open

    @property
    def is_bearish(self) -> bool:
        return self.close < self.open

    @property
    def body(self) -> float:
        return abs(self.close - self.open)

    @property
    def full_range(self) -> float:
        return self.high - self.low

    @property
    def upper_wick(self) -> float:
        return self.high - max(self.open, self.close)

    @property
    def lower_wick(self) -> float:
        return min(self.open, self.close) - self.low

    @property
    def midpoint(self) -> float:
        return (self.high + self.low) / 2

    @property
    def direction(self) -> int:
        """+1 bullish, -1 bearish, 0 doji."""
        if self.close > self.open:
            return 1
        if self.close < self.open:
            return -1
        return 0
