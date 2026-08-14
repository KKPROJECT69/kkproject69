"""Fair Value Gap (FVG) strategy."""
from __future__ import annotations

from ...analysis.market_analyzer import MarketAnalysis
from ...models.candle import Candle
from ...models.enums import Direction
from ...models.signal import StrategyResult
from ..base import Strategy


class FairValueGap(Strategy):
    id = "fvg"
    name = "Fair Value Gap"

    def analyze(self, analysis: MarketAnalysis, candles: list[Candle]) -> StrategyResult:
        # TODO: confirm exact rules vs original spec
        close = analysis.last_close
        for gap in reversed(analysis.fvg):
            top = gap["top"]
            bottom = gap["bottom"]
            if gap["type"] == "bullish" and bottom <= close <= top:
                return StrategyResult(
                    self.id, self.name, Direction.CALL, 74.0,
                    reason="Price re-entered a bullish fair value gap",
                    risks=["Gap may be fully filled and reverse"],
                    invalidation=["Close below the gap bottom"],
                    evidence={"fvg_top": top, "fvg_bottom": bottom},
                )
            if gap["type"] == "bearish" and bottom <= close <= top:
                return StrategyResult(
                    self.id, self.name, Direction.PUT, 74.0,
                    reason="Price re-entered a bearish fair value gap",
                    risks=["Gap may be fully filled and reverse"],
                    invalidation=["Close above the gap top"],
                    evidence={"fvg_top": top, "fvg_bottom": bottom},
                )
        return StrategyResult(self.id, self.name, Direction.NO_TRADE, 20.0, reason="No active FVG")
