"""Risk Control overlay (market-condition gate, not directional).

Evaluates volatility / market condition and contributes a risk classification
without producing directional evidence. TODO: confirm risk thresholds.
"""
from __future__ import annotations

from ..base import Strategy
from ...analysis.market_analyzer import MarketAnalysis
from ...models.candle import Candle
from ...models.enums import Direction
from ...models.signal import StrategyResult


class RiskControl(Strategy):
    id = "risk_control"
    name = "Risk Control"

    def analyze(self, analysis: MarketAnalysis, candles: list[Candle]) -> StrategyResult:
        # TODO: confirm exact risk thresholds vs original spec
        ratio = analysis.volatility / analysis.last_close if analysis.last_close else 0.0
        if ratio > 0.015:
            level = "HIGH"
        elif ratio > 0.008:
            level = "MEDIUM"
        else:
            level = "LOW"
        return StrategyResult(
            self.id,
            self.name,
            Direction.NO_TRADE,
            100.0,
            reason=f"Risk overlay: {level} volatility regime ({ratio * 100:.2f}%)",
            risks=[f"{level} volatility regime — size accordingly"],
            evidence={"risk_level": level, "volatility_ratio": round(ratio, 4)},
        )
