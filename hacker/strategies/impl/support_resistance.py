"""Support & Resistance strategy."""
from __future__ import annotations

from ...analysis.market_analyzer import MarketAnalysis
from ...models.candle import Candle
from ...models.enums import Direction
from ...models.signal import StrategyResult
from ..base import Strategy


class SupportResistance(Strategy):
    id = "support_resistance"
    name = "Support & Resistance"

    def analyze(self, analysis: MarketAnalysis, candles: list[Candle]) -> StrategyResult:
        # TODO: confirm exact entry/confirmation/invalidation rules vs original spec
        close = analysis.last_close
        atr = analysis.volatility or (close * 0.002) or 1.0
        supports = [s for s in analysis.support_levels if s <= close]
        resistances = [r for r in analysis.resistance_levels if r >= close]
        nearest_support = max(supports) if supports else None
        nearest_resistance = min(resistances) if resistances else None

        if (
            nearest_support is not None
            and (close - nearest_support) <= 0.4 * atr
            and candles
            and candles[-1].is_bullish
        ):
            return StrategyResult(
                self.id, self.name, Direction.CALL, 72.0,
                reason=f"Price bounced near support {nearest_support:.4f}",
                risks=["Support may break to the downside"],
                invalidation=["Close below support"],
                evidence={"support": nearest_support},
            )
        if (
            nearest_resistance is not None
            and (nearest_resistance - close) <= 0.4 * atr
            and candles
            and candles[-1].is_bearish
        ):
                return StrategyResult(
                    self.id, self.name, Direction.PUT, 72.0,
                    reason=f"Price rejected near resistance {nearest_resistance:.4f}",
                    risks=["Resistance may break to the upside"],
                    invalidation=["Close above resistance"],
                    evidence={"resistance": nearest_resistance},
                )
        return StrategyResult(self.id, self.name, Direction.NO_TRADE, 30.0,
                              reason="Price is mid-range away from key levels")
