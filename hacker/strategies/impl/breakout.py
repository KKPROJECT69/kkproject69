"""Breakout strategy."""
from __future__ import annotations

from ...analysis.market_analyzer import MarketAnalysis
from ...models.candle import Candle
from ...models.enums import Direction
from ...models.signal import StrategyResult
from ..base import Strategy


class Breakout(Strategy):
    id = "breakout"
    name = "Breakout"

    def analyze(self, analysis: MarketAnalysis, candles: list[Candle]) -> StrategyResult:
        # TODO: confirm exact rules vs original spec
        close = analysis.last_close
        avg_vol = sum(c.volume for c in candles[-20:]) / max(len(candles[-20:]), 1)
        last_vol = candles[-1].volume if candles else 0.0
        volume_ok = last_vol >= avg_vol * 1.2

        if close > analysis.breakout_level and volume_ok:
            return StrategyResult(
                self.id, self.name, Direction.CALL, 78.0,
                reason=f"Close {close:.4f} broke above resistance {analysis.breakout_level:.4f} on volume",
                risks=["False breakout / wick rejection"],
                invalidation=["Close back below the breakout level"],
                evidence={"breakout_level": analysis.breakout_level},
            )
        if close < analysis.breakdown_level and volume_ok:
            return StrategyResult(
                self.id, self.name, Direction.PUT, 78.0,
                reason=f"Close {close:.4f} broke below support {analysis.breakdown_level:.4f} on volume",
                risks=["False breakdown / wick rejection"],
                invalidation=["Close back above the breakdown level"],
                evidence={"breakdown_level": analysis.breakdown_level},
            )
        return StrategyResult(self.id, self.name, Direction.NO_TRADE, 15.0, reason="No confirmed breakout")
