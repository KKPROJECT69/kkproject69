"""Strategy interface.

Each strategy MUST expose direction, confidence, reason, risks and
invalidation. Overlay strategies (money management / risk control) may return
NO_TRADE as a gate while still contributing risk guidance; the aggregator
ignores NO_TRADE outputs as directional evidence.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from ..analysis.market_analyzer import MarketAnalysis
from ..models.candle import Candle
from ..models.signal import StrategyResult


class Strategy(ABC):
    id: str = "base"
    name: str = "Base"

    @abstractmethod
    def analyze(self, analysis: MarketAnalysis, candles: list[Candle]) -> StrategyResult:
        """Produce a structured strategy result for the given market context."""

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Strategy {self.id}>"
