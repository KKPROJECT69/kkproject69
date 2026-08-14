"""AI service layer — reasoning / approval for approved signals.

Default implementation is an offline, rule-based reviewer so the pipeline is
fully functional without an external AI API. Swap in `HttpAIService` once an
AI endpoint + key are configured.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from ..analysis.market_analyzer import MarketAnalysis
from ..models.enums import Direction
from ..models.signal import AggregateEvidence


@dataclass
class AIApproval:
    approved: bool
    verdict: str
    reasoning: str


class AIService(ABC):
    @abstractmethod
    def approve(
        self,
        direction: Direction,
        evidence: AggregateEvidence,
        analysis: MarketAnalysis,
    ) -> AIApproval:
        """Return a final verdict + human-readable reasoning."""


class RuleBasedAIService(AIService):
    """Offline AI stand-in. Approves any non-NO_TRADE directional setup that
    already cleared the confidence/conflict gates, with deterministic wording."""

    def approve(
        self,
        direction: Direction,
        evidence: AggregateEvidence,
        analysis: MarketAnalysis,
    ) -> AIApproval:
        if direction == Direction.NO_TRADE:
            return AIApproval(False, "NO TRADE", "No valid directional setup was approved.")
        supporting = ", ".join(evidence.supporting) or "combined evidence"
        risks = "; ".join(evidence.risks) if evidence.risks else "none flagged"
        reasoning = (
            f"Trend {analysis.trend.lower()}, structure {analysis.structure.lower()}, "
            f"RSI {analysis.rsi:.0f}. {len(evidence.supporting)} of "
            f"{evidence.total_directional} directional strategies agree "
            f"({evidence.agreement * 100:.0f}% agreement, {evidence.confidence:.0f}% confidence). "
            f"Supporting: {supporting}. Risks: {risks}."
        )
        verdict = f"STRONG {direction.value}"
        return AIApproval(True, verdict, reasoning)


class HttpAIService(AIService):
    """Remote AI approval — TODO: wire to AI_API_URL / AI_API_KEY."""

    def approve(
        self,
        direction: Direction,
        evidence: AggregateEvidence,
        analysis: MarketAnalysis,
    ) -> AIApproval:
        # Placeholder: a remote AI gateway would be called here.
        return RuleBasedAIService().approve(direction, evidence, analysis)
