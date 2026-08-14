"""Per-user conversation state (in-memory) for the button-first UI."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from ..models.enums import Timeframe
from ..paper import PaperTradingEngine
from ..results.statistics import SessionStatistics


@dataclass
class UserState:
    user_id: int
    pending_action: str | None = None
    pair: str = "USDBDT-OTC"
    timeframe: Timeframe = Timeframe.M1
    strategy_id: str | None = None
    min_payout: float = 0.0
    skip_news: bool = False
    session_active: bool = False
    session_type: str | None = None
    session_task: asyncio.Task | None = None
    session_stats: SessionStatistics = field(default_factory=SessionStatistics)
    session_id: str | None = None
    paper: PaperTradingEngine = field(default_factory=PaperTradingEngine)


class StateStore:
    def __init__(self) -> None:
        self._states: dict[int, UserState] = {}

    def get(self, user_id: int) -> UserState:
        if user_id not in self._states:
            self._states[user_id] = UserState(user_id=user_id)
        return self._states[user_id]
