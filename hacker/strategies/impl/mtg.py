"""MTG methodology strategy (trend-aligned, recovery-aware entries).

The MTG (Martingale-style recovery) methodology from the project history is a
money-management/recovery discipline. This module produces conservative,
trend-aligned entries that are MTG-compatible and carries the recovery context
in its risk notes. TODO: confirm against the authoritative MTG rules.
"""
from __future__ import annotations

from ...analysis.market_analyzer import MarketAnalysis
from ...models.candle import Candle
from ...models.enums import Direction
from ...models.signal import StrategyResult
from ..base import Strategy


class MTG(Strategy):
    id = "mtg"
    name = "MTG Methodology"

    def analyze(self, analysis: MarketAnalysis, candles: list[Candle]) -> StrategyResult:
        # TODO: confirm exact MTG entry/recovery rules vs original spec
        if analysis.trend == "UP" and analysis.rsi < 65:
            return StrategyResult(
                self.id, self.name, Direction.CALL, 66.0,
                reason="Uptrend pullback — MTG-compatible entry",
                risks=["MTG recovery path applies if this entry loses"],
                invalidation=["Trend flips to DOWN"],
                evidence={"trend": analysis.trend, "rsi": analysis.rsi},
            )
        if analysis.trend == "DOWN" and analysis.rsi > 35:
            return StrategyResult(
                self.id, self.name, Direction.PUT, 66.0,
                reason="Downtrend retrace — MTG-compatible entry",
                risks=["MTG recovery path applies if this entry loses"],
                invalidation=["Trend flips to UP"],
                evidence={"trend": analysis.trend, "rsi": analysis.rsi},
            )
        return StrategyResult(self.id, self.name, Direction.NO_TRADE, 20.0, reason="No MTG-compatible setup")
