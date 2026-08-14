"""Volume Imbalance strategy."""
from __future__ import annotations

from ..base import Strategy
from ...analysis.market_analyzer import MarketAnalysis
from ...models.candle import Candle
from ...models.enums import Direction
from ...models.signal import StrategyResult


class VolumeImbalance(Strategy):
    id = "volume_imbalance"
    name = "Volume Imbalance"

    def analyze(self, analysis: MarketAnalysis, candles: list[Candle]) -> StrategyResult:
        # TODO: confirm exact rules vs original spec
        if len(candles) < 20:
            return StrategyResult(self.id, self.name, Direction.NO_TRADE, 0.0, reason="Not enough data")
        avg_vol = sum(c.volume for c in candles[-20:]) / 20
        last = candles[-1]
        ratio = last.volume / avg_vol if avg_vol else 0.0
        if ratio < 1.5:
            return StrategyResult(self.id, self.name, Direction.NO_TRADE, 10.0, reason="No volume imbalance")
        if last.is_bullish and last.body > last.full_range * 0.6:
            return StrategyResult(
                self.id, self.name, Direction.CALL, 70.0,
                reason=f"Bullish imbalance candle with {ratio:.1f}x average volume",
                risks=["Climax volume may exhaust"],
                invalidation=["Close below the imbalance candle low"],
                evidence={"volume_ratio": round(ratio, 2)},
            )
        if last.is_bearish and last.body > last.full_range * 0.6:
            return StrategyResult(
                self.id, self.name, Direction.PUT, 70.0,
                reason=f"Bearish imbalance candle with {ratio:.1f}x average volume",
                risks=["Climax volume may exhaust"],
                invalidation=["Close above the imbalance candle high"],
                evidence={"volume_ratio": round(ratio, 2)},
            )
        return StrategyResult(self.id, self.name, Direction.NO_TRADE, 10.0, reason="No directional imbalance")
