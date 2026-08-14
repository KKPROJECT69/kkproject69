"""Confidence weighting from measured performance — safe, local learning.

Each strategy's historical win-rate becomes a 0..1 weight (Laplace-smoothed so
a strategy with no history is neutral). Weights scale a strategy's confidence
*before* aggregation. The hard 70% gate still applies afterward, so learning
can never bypass the safety rules.
"""
from __future__ import annotations

from ..backtest.engine import BacktestReport
from ..models.enums import ResultType
from ..storage.repositories import StatsRepo


class ConfidenceWeights:
    def __init__(self, smoothing: float = 1.0) -> None:
        self.smoothing = smoothing

    def from_backtest(self, report: BacktestReport) -> dict[str, float]:
        weights: dict[str, float] = {}
        for sid, stat in report.by_strategy.items():
            weights[sid] = (stat.wins + self.smoothing) / (
                stat.wins + stat.losses + 2 * self.smoothing
            )
        return weights

    async def from_stats(self, stats_repo: StatsRepo) -> dict[str, float]:
        rows = await stats_repo.get_all()
        weights: dict[str, float] = {}
        for row in rows:
            wins = row.get("wins", 0) + row.get("mtg_wins", 0)
            losses = row.get("losses", 0)
            weights[row["strategy_id"]] = (wins + self.smoothing) / (
                wins + losses + 2 * self.smoothing
            )
        return weights

    def apply(self, results: list, weights: dict[str, float]) -> list:
        """Return a copy of results with confidence scaled by weight."""
        adjusted = []
        for r in results:
            w = weights.get(r.strategy_id)
            if w is None or not r.is_directional:
                adjusted.append(r)
                continue
            import copy

            rr = copy.copy(r)
            rr.confidence = round(min(100.0, r.confidence * w * 2), 2)
            adjusted.append(rr)
        return adjusted
