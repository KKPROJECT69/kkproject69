"""Market Structure strategy (break of structure with trend)."""
from __future__ import annotations

from ..base import Strategy
from ...analysis.market_analyzer import MarketAnalysis
from ...models.candle import Candle
from ...models.enums import Direction
from ...models.signal import StrategyResult


class MarketStructure(Strategy):
    id = "market_structure"
    name = "Market Structure"

    def analyze(self, analysis: MarketAnalysis, candles: list[Candle]) -> StrategyResult:
        # TODO: confirm exact rules vs original spec
        if analysis.structure == "BULLISH" and analysis.trend in ("UP",):
            return StrategyResult(
                self.id, self.name, Direction.CALL, 69.0,
                reason="Bullish structure (HH-HL) aligned with uptrend",
                risks=["Structure shift to the downside"],
                invalidation=["Break of the latest higher low"],
                evidence={"structure": analysis.structure, "trend": analysis.trend},
            )
        if analysis.structure == "BEARISH" and analysis.trend in ("DOWN",):
            return StrategyResult(
                self.id, self.name, Direction.PUT, 69.0,
                reason="Bearish structure (LH-LL) aligned with downtrend",
                risks=["Structure shift to the upside"],
                invalidation=["Break of the latest lower high"],
                evidence={"structure": analysis.structure, "trend": analysis.trend},
            )
        return StrategyResult(self.id, self.name, Direction.NO_TRADE, 20.0, reason="Structure and trend not aligned")
