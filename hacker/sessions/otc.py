"""OTC future-signal workflow — OTC pairs via the configured OTC source."""
from __future__ import annotations

from ..models.enums import Timeframe
from ..models.signal import FinalSignal
from ..pipeline import SignalPipeline


class OTCFutureSignalService:
    def __init__(self, pipeline: SignalPipeline, default_pair: str = "USDBDT_otc") -> None:
        self.pipeline = pipeline
        self.default_pair = default_pair

    async def future_signal(
        self,
        pair: str | None = None,
        timeframe: Timeframe = Timeframe.M1,
        user_id: int | None = None,
    ) -> FinalSignal | None:
        return await self.pipeline.generate(
            pair or self.default_pair,
            timeframe,
            context={"otc": True},
            user_id=user_id,
        )
