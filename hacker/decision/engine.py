"""Signal decision engine — evidence → CALL / PUT / NO_TRADE."""
from __future__ import annotations

from ..analysis.market_analyzer import MarketAnalysis
from ..models.enums import Direction
from ..models.signal import Decision, StrategyResult
from .ai import AIApproval, AIService, RuleBasedAIService
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

    # ---- shared helpers -------------------------------------------------
    def _evidence(self, results: list[StrategyResult]) -> tuple:
        evidence = self.aggregator.aggregate(results)
        confidence = combine_confidence(evidence)
        return evidence, confidence

    def _rejection(self, evidence, confidence: float) -> Decision | None:
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
        return None

    def _finalize(
        self,
        direction: Direction,
        evidence,
        confidence: float,
        approval: AIApproval,
    ) -> Decision:
        approved = approval.approved and direction in (Direction.CALL, Direction.PUT)
        return Decision(
            direction=direction,
            confidence=confidence,
            approved=approved,
            verdict=approval.verdict,
            reasoning=approval.reasoning,
            supporting_strategies=evidence.supporting,
            conflicts=[],
            risks=evidence.risks,
        )

    # ---- decision entry points ------------------------------------------
    def decide(
        self,
        results: list[StrategyResult],
        analysis: MarketAnalysis,
        context: dict | None = None,
    ) -> Decision:
        """Synchronous decision (local AI only)."""
        del context
        evidence, confidence = self._evidence(results)
        rejection = self._rejection(evidence, confidence)
        if rejection is not None:
            return rejection
        approval = self.ai.approve(evidence.direction, evidence, analysis)
        return self._finalize(evidence.direction, evidence, confidence, approval)

    async def decide_async(
        self,
        results: list[StrategyResult],
        analysis: MarketAnalysis,
        context: dict | None = None,
    ) -> Decision:
        """Async decision (respects the configured AI provider)."""
        del context
        evidence, confidence = self._evidence(results)
        rejection = self._rejection(evidence, confidence)
        if rejection is not None:
            return rejection
        approval = await self.ai.approve_async(evidence.direction, evidence, analysis)
        return self._finalize(evidence.direction, evidence, confidence, approval)
