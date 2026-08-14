"""Strategy performance tracking + safe learning.

Learning records outcomes and exposes performance statistics. It must NEVER
bypass the core safety gates (confidence / conflict / filters).
"""
from __future__ import annotations

from ..models.enums import ResultType
from ..storage.repositories import StatsRepo


class StrategyPerformance:
    def __init__(self, stats_repo: StatsRepo) -> None:
        self.stats_repo = stats_repo

    async def record(self, strategy_id: str, pair: str, result: ResultType) -> None:
        await self.stats_repo.record(strategy_id, pair, result)

    async def report(self) -> list[dict]:
        return await self.stats_repo.get_all()
