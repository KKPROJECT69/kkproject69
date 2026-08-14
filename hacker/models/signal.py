"""Signal-domain dataclasses: strategy results, aggregated evidence, decisions, final signals."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from .enums import Direction, RiskLevel, Timeframe


@dataclass
class StrategyResult:
    """A single strategy's structured output.

    Overlay strategies (money management, risk control) may return
    Direction.NO_TRADE as a *gate* while still contributing risks/evidence.
    """

    strategy_id: str
    name: str
    direction: Direction
    confidence: float  # 0-100
    reason: str = ""
    risks: list[str] = field(default_factory=list)
    invalidation: list[str] = field(default_factory=list)
    evidence: dict = field(default_factory=dict)

    @property
    def is_directional(self) -> bool:
        return self.direction in (Direction.CALL, Direction.PUT)


@dataclass
class AggregateEvidence:
    direction: Direction
    confidence: float
    agreement: float  # 0..1
    conflicting: bool
    supporting: list[str] = field(default_factory=list)
    opposing: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    total_directional: int = 0
    total_active: int = 0


@dataclass
class Decision:
    direction: Direction
    confidence: float
    approved: bool
    verdict: str = ""
    reasoning: str = ""
    supporting_strategies: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)


@dataclass
class FinalSignal:
    pair: str
    direction: Direction
    timeframe: Timeframe
    target_entry: datetime
    confidence: float
    payout: float | None = None
    strategy: str = ""
    reason: str = ""
    ai_verdict: str = ""
    risk_level: str = RiskLevel.MEDIUM.value
    session_id: str | None = None
    user_id: int | None = None
    generated_at: datetime | None = None
    signal_id: str | None = None
