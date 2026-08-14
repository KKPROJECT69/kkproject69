"""Trendline strategy (linear-regression trend line touch)."""
from __future__ import annotations

from ..base import Strategy
from ...analysis.market_analyzer import MarketAnalysis
from ...models.candle import Candle
from ...models.enums import Direction
from ...models.signal import StrategyResult


def _linreg(values: list[float]) -> tuple[float, float]:
    n = len(values)
    x = list(range(n))
    x_mean = sum(x) / n
    y_mean = sum(values) / n
    num = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
    den = sum((x[i] - x_mean) ** 2 for i in range(n))
    slope = num / den if den else 0.0
    intercept = y_mean - slope * x_mean
    return slope, intercept


class Trendline(Strategy):
    id = "trendline"
    name = "Trendline"

    def analyze(self, analysis: MarketAnalysis, candles: list[Candle]) -> StrategyResult:
        # TODO: confirm exact rules vs original spec
        if len(candles) < 20:
            return StrategyResult(self.id, self.name, Direction.NO_TRADE, 0.0, reason="Not enough data")
        closes = [c.close for c in candles]
        slope, intercept = _linreg(closes)
        last_x = len(closes) - 1
        line_at_last = intercept + slope * last_x
        closeness = abs(analysis.last_close - line_at_last) / (line_at_last or 1)
        if slope > 0 and closeness < 0.01 and analysis.trend in ("UP",):
            return StrategyResult(
                self.id, self.name, Direction.CALL, 68.0,
                reason="Price holds above a rising trendline",
                risks=["Trendline break to the downside"],
                invalidation=["Close below trendline"],
                evidence={"slope": round(slope, 6)},
            )
        if slope < 0 and closeness < 0.01 and analysis.trend in ("DOWN",):
            return StrategyResult(
                self.id, self.name, Direction.PUT, 68.0,
                reason="Price rejects a falling trendline",
                risks=["Trendline break to the upside"],
                invalidation=["Close above trendline"],
                evidence={"slope": round(slope, 6)},
            )
        return StrategyResult(self.id, self.name, Direction.NO_TRADE, 25.0, reason="No trendline touch")
