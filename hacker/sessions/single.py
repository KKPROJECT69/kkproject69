"""Single-strategy live session — one selected strategy on selected pairs."""
from __future__ import annotations

import asyncio
import logging

from ..models.enums import Timeframe
from ..pipeline import SignalPipeline
from .manager import Session, SessionManager

log = logging.getLogger(__name__)


class SingleStrategySessionService:
    def __init__(
        self,
        pipeline: SignalPipeline,
        manager: SessionManager,
        timeframe: Timeframe = Timeframe.M1,
        interval_seconds: float = 5.0,
    ) -> None:
        self.pipeline = pipeline
        self.manager = manager
        self.timeframe = timeframe
        self.interval_seconds = interval_seconds

    async def run(self, session: Session) -> None:
        log.info(
            "Single-strategy session %s (%s) started for user %s",
            session.id,
            session.strategy_id,
            session.user_id,
        )
        while self.manager.is_running(session.user_id):
            for pair in session.pairs:
                await self.pipeline.generate(
                    pair,
                    self.timeframe,
                    strategy_ids=[session.strategy_id] if session.strategy_id else None,
                    session_id=session.id,
                    user_id=session.user_id,
                )
            await asyncio.sleep(self.interval_seconds)
        log.info("Single-strategy session %s stopped", session.id)
