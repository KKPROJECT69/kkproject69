"""Fakeout strategy (failed breakout fade)."""
from __future__ import annotations

from ...analysis.market_analyzer import MarketAnalysis
from ...models.candle import Candle
from ...models.enums import Direction
from ...models.signal import StrategyResult
from ..base import Strategy


class Fakeout(Strategy):
    id = "fakeout"
    name = "Fakeout"

    def analyze(self, analysis: MarketAnalysis, candles: list[Candle]) -> StrategyResult:
        # TODO: confirm exact rules vs original spec
        if len(candles) < 3:
            return StrategyResult(self.id, self.name, Direction.NO_TRADE, 0.0, reason="Not enough data")
        prev = candles[-2]
        last = candles[-1]
        # Fake breakout: prev spiked above resistance but closed back under it
        if (
            prev.high > analysis.breakout_level
            and prev.close < analysis.breakout_level
            and last.is_bearish
        ):
            return StrategyResult(
                self.id, self.name, Direction.PUT, 71.0,
                reason="Fake breakout above resistance — fading back down",
                risks=["Move may resume upward"],
                invalidation=["Close above the fakeout high"],
                evidence={"level": analysis.breakout_level},
            )
        # Fake breakdown: prev spiked below support but closed back over it
        if (
            prev.low < analysis.breakdown_level
            and prev.close > analysis.breakdown_level
            and last.is_bullish
        ):
                return StrategyResult(
                    self.id, self.name, Direction.CALL, 71.0,
                    reason="Fake breakdown below support — fading back up",
                    risks=["Move may resume downward"],
                    invalidation=["Close below the fakeout low"],
                    evidence={"level": analysis.breakdown_level},
                )
        return StrategyResult(self.id, self.name, Direction.NO_TRADE, 10.0, reason="No fakeout pattern")
