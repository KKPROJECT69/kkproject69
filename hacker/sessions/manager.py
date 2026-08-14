"""Per-user session lifecycle. One active session per user (isolated)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4

from ..models.enums import SessionStatus
from ..storage.repositories import SessionRepo


@dataclass
class Session:
    id: str
    user_id: int
    type: str
    strategy_id: str | None = None
    pairs: list[str] = field(default_factory=list)
    status: SessionStatus = SessionStatus.IDLE
    started_at: datetime | None = None


class SessionManager:
    def __init__(self, repo: SessionRepo) -> None:
        self.repo = repo
        self._active: dict[int, Session] = {}

    async def start(
        self,
        user_id: int,
        session_type: str,
        strategy_id: str | None = None,
        pairs: list[str] | None = None,
    ) -> Session:
        session = Session(
            id=uuid4().hex[:12],
            user_id=user_id,
            type=session_type,
            strategy_id=strategy_id,
            pairs=pairs or [],
            status=SessionStatus.RUNNING,
            started_at=datetime.now(UTC),
        )
        await self.repo.create(
            session.id, user_id, session_type, strategy_id, session.pairs
        )
        self._active[user_id] = session
        return session

    async def stop(self, user_id: int) -> Session | None:
        session = self._active.pop(user_id, None)
        if session is not None:
            await self.repo.set_status(session.id, SessionStatus.STOPPED)
        return session

    def get(self, user_id: int) -> Session | None:
        return self._active.get(user_id)

    def is_running(self, user_id: int) -> bool:
        return user_id in self._active

    def status(self, user_id: int) -> str:
        session = self._active.get(user_id)
        return session.status.value if session else SessionStatus.IDLE.value
