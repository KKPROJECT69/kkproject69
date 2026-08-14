"""AI loss review — deterministic rule-based review for offline operation."""
from __future__ import annotations

from ..analysis.market_analyzer import MarketAnalysis
from ..models.enums import Direction


class LossReviewer:
    def review(
        self,
        direction: Direction,
        analysis: MarketAnalysis,
        realized_result: str,
    ) -> dict:
        if direction == Direction.CALL and analysis.trend == "DOWN":
            failure = "Counter-trend CALL in a DOWN market"
        elif direction == Direction.PUT and analysis.trend == "UP":
            failure = "Counter-trend PUT in an UP market"
        elif analysis.rsi >= 70:
            failure = "Overbought entry — momentum exhausted"
        elif analysis.rsi <= 30:
            failure = "Oversold entry — momentum exhausted"
        else:
            failure = "Setup invalidated by market structure shift"

        return {
            "failure_reason": failure,
            "strategy_impact": "confidence weighting reduced for the involved strategy",
            "learning": "avoid counter-trend entries without confirmation",
            "strategy_status": "under review",
            "realized_result": realized_result,
        }
