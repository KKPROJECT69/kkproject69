"""Confidence engine — the 70% gate and evidence blending."""
from __future__ import annotations

from ..models.signal import AggregateEvidence


def combine_confidence(evidence: AggregateEvidence) -> float:
    """Blend raw average confidence with inter-strategy agreement."""
    if evidence.conflicting or evidence.total_directional == 0:
        return 0.0
    agreement_boost = 0.6 + 0.4 * evidence.agreement
    return round(min(100.0, evidence.confidence * agreement_boost), 2)


def passes_gate(confidence: float, min_confidence: float = 70.0) -> bool:
    return confidence >= min_confidence
