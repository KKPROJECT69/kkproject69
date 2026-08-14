"""Combine the 11 strategies into a single structured evidence picture."""
from __future__ import annotations

from ..models.enums import Direction
from ..models.signal import AggregateEvidence, StrategyResult


class StrategyAggregator:
    def __init__(self, conflict_threshold: float = 50.0) -> None:
        self.conflict_threshold = conflict_threshold

    def aggregate(
        self,
        results: list[StrategyResult],
        weights: dict[str, float] | None = None,
    ) -> AggregateEvidence:
        weights = weights or {}
        directional = []
        for r in results:
            if not r.is_directional:
                continue
            rr = r
            w = weights.get(r.strategy_id)
            if w is not None:
                import copy

                rr = copy.copy(r)
                rr.confidence = round(min(100.0, r.confidence * w * 2), 2)
            directional.append(rr)
        calls = [r for r in directional if r.direction == Direction.CALL]
        puts = [r for r in directional if r.direction == Direction.PUT]
        risks: list[str] = []
        for r in results:
            risks.extend(r.risks)

        total = len(directional)
        if total == 0:
            return AggregateEvidence(
                direction=Direction.NO_TRADE,
                confidence=0.0,
                agreement=0.0,
                conflicting=False,
                risks=risks,
                total_directional=0,
                total_active=len(results),
            )

        if calls and puts:
            call_conf = sum(r.confidence for r in calls) / len(calls)
            put_conf = sum(r.confidence for r in puts) / len(puts)
            majority = calls if len(calls) >= len(puts) else puts
            minority = puts if majority is calls else calls
            conflicting = min(call_conf, put_conf) >= self.conflict_threshold
            direction = majority[0].direction
            supporting = [r.name for r in majority]
            opposing = [r.name for r in minority]
            confidence = 0.0 if conflicting else sum(r.confidence for r in directional) / total
        else:
            direction = directional[0].direction
            supporting = [r.name for r in directional]
            opposing = []
            conflicting = False
            confidence = sum(r.confidence for r in directional) / total

        agreement = len([r for r in directional if r.direction == direction]) / total
        return AggregateEvidence(
            direction=direction,
            confidence=round(confidence, 2),
            agreement=round(agreement, 2),
            conflicting=conflicting,
            supporting=supporting,
            opposing=opposing,
            risks=risks,
            total_directional=total,
            total_active=len(results),
        )
