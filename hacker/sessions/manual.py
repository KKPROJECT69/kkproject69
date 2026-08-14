"""Manual live signal service — one strategy, one pair, on demand."""
from __future__ import annotations

from ..models.enums import Timeframe
from ..models.signal import FinalSignal
from ..pipeline import SignalPipeline


class ManualSignalService:
    def __init__(self, pipeline: SignalPipeline) -> None:
        self.pipeline = pipeline

    async def signal(
        self,
        pair: str,
        timeframe: Timeframe,
        strategy_id: str | None = None,
        user_id: int | None = None,
    ) -> FinalSignal | None:
        return await self.pipeline.generate(
            pair,
            timeframe,
            strategy_ids=[strategy_id] if strategy_id else None,
            user_id=user_id,
        )
