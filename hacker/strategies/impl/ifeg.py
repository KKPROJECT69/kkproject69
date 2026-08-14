"""IFEG strategy (inducement / fair-entry gap — liquidity sweep + displacement).

NOTE: the exact IFEG definition was not retrievable from the project docs.
This is a placeholder heuristic: a liquidity sweep (prior swing taken) followed
by a strong displacement candle implies continuation in the displacement
direction. TODO: replace with the authoritative IFEG rules.
"""
from __future__ import annotations

from ...analysis.market_analyzer import MarketAnalysis
from ...models.candle import Candle
from ...models.enums import Direction
from ...models.signal import StrategyResult
from ..base import Strategy


class IFEG(Strategy):
    id = "ifeg"
    name = "IFEG"

    def analyze(self, analysis: MarketAnalysis, candles: list[Candle]) -> StrategyResult:
        # TODO: replace with the authoritative IFEG rules
        if len(candles) < 5:
            return StrategyResult(self.id, self.name, Direction.NO_TRADE, 0.0, reason="Not enough data")
        last = candles[-1]
        prior_low = min(c.low for c in candles[-5:-1])
        prior_high = max(c.high for c in candles[-5:-1])
        if candles[-2].low < prior_low and last.is_bullish and last.body > (last.full_range * 0.5):
            return StrategyResult(
                self.id, self.name, Direction.CALL, 73.0,
                reason="Liquidity sweep below prior low followed by bullish displacement",
                risks=["Sweep may not hold"],
                invalidation=["Close below the sweep low"],
                evidence={"sweep_low": prior_low},
            )
        if candles[-2].high > prior_high and last.is_bearish and last.body > (last.full_range * 0.5):
            return StrategyResult(
                self.id, self.name, Direction.PUT, 73.0,
                reason="Liquidity sweep above prior high followed by bearish displacement",
                risks=["Sweep may not hold"],
                invalidation=["Close above the sweep high"],
                evidence={"sweep_high": prior_high},
            )
        return StrategyResult(self.id, self.name, Direction.NO_TRADE, 15.0, reason="No IFEG sweep+displacement")
