"""Signal decision engine — evidence → CALL / PUT / NO_TRADE."""
from __future__ import annotations

from ..analysis.market_analyzer import MarketAnalysis
from ..models.enums import Direction
from ..models.signal import Decision, StrategyResult
from .ai import AIService, RuleBasedAIService
from .confidence import combine_confidence
from ..strategies.aggregator import StrategyAggregator


class SignalDecisionEngine:
    def __init__(
        self,
        aggregator: StrategyAggregator | None = None,
        ai: AIService | None = None,
        min_confidence: float = 70.0,
    ) -> None:
        self.aggregator = aggregator or StrategyAggregator()
        self.ai = ai or RuleBasedAIService()
        self.min_confidence = min_confidence

    def decide(
        self,
        results: list[StrategyResult],
        analysis: MarketAnalysis,
        context: dict | None = None,
    ) -> Decision:
        del context  # reserved for news/payout context expansion
        evidence = self.aggregator.aggregate(results)
        confidence = combine_confidence(evidence)

        if evidence.conflicting:
            return Decision(
                direction=Direction.NO_TRADE,
                confidence=confidence,
                approved=False,
                verdict="NO TRADE",
                reasoning="Conflicting BUY/SELL evidence — rejected.",
                supporting_strategies=evidence.supporting,
                conflicts=evidence.opposing,
                risks=evidence.risks,
            )

        if evidence.total_directional == 0:
            return Decision(
                direction=Direction.NO_TRADE,
                confidence=0.0,
                approved=False,
                verdict="NO TRADE",
                reasoning="No directional strategy evidence.",
                risks=evidence.risks,
            )

        if confidence < self.min_confidence:
            return Decision(
                direction=Direction.NO_TRADE,
                confidence=confidence,
                approved=False,
                verdict="NO TRADE",
                reasoning=(
                    f"Confidence {confidence:.0f}% is below the "
                    f"{self.min_confidence:.0f}% minimum gate."
                ),
                supporting_strategies=evidence.supporting,
                risks=evidence.risks,
            )

        ai_approval = self.ai.approve(evidence.direction, evidence, analysis)
        approved = ai_approval.approved and evidence.direction in (Direction.CALL, Direction.PUT)
        return Decision(
            direction=evidence.direction,
            confidence=confidence,
            approved=approved,
            verdict=ai_approval.verdict,
            reasoning=ai_approval.reasoning,
            supporting_strategies=evidence.supporting,
            conflicts=[],
            risks=evidence.risks,
        )
