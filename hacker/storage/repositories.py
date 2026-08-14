"""Thin repository layer over the SQLite Database."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from ..models.enums import AccessLevel, ResultType, SessionStatus
from .db import Database


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class UserRepo:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def get(self, telegram_id: int) -> dict[str, Any] | None:
        return await self.db.fetchone(
            "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
        )

    async def upsert(
        self,
        telegram_id: int,
        username: str | None = None,
        access_level: AccessLevel = AccessLevel.FREE,
    ) -> None:
        await self.db.execute(
            """
            INSERT INTO users (telegram_id, username, access_level, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET username = excluded.username
            """,
            (telegram_id, username, access_level.value, _now()),
        )

    async def set_level(self, telegram_id: int, level: AccessLevel) -> None:
        await self.db.execute(
            "UPDATE users SET access_level = ? WHERE telegram_id = ?",
            (level.value, telegram_id),
        )

    async def set_settings(self, telegram_id: int, settings: dict) -> None:
        await self.db.execute(
            "UPDATE users SET settings_json = ? WHERE telegram_id = ?",
            (json.dumps(settings), telegram_id),
        )

    async def get_settings(self, telegram_id: int) -> dict:
        row = await self.get(telegram_id)
        if row and row.get("settings_json"):
            return json.loads(row["settings_json"])
        return {}


class SessionRepo:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def create(
        self,
        session_id: str,
        user_id: int,
        session_type: str,
        strategy_id: str | None = None,
        pairs: list[str] | None = None,
    ) -> None:
        await self.db.execute(
            "INSERT INTO sessions (id, user_id, type, strategy_id, pairs, status, started_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                session_id,
                user_id,
                session_type,
                strategy_id,
                json.dumps(pairs or []),
                SessionStatus.RUNNING.value,
                _now(),
            ),
        )

    async def set_status(self, session_id: str, status: SessionStatus) -> None:
        await self.db.execute(
            "UPDATE sessions SET status = ?, ended_at = ? WHERE id = ?",
            (status.value, _now(), session_id),
        )

    async def get(self, session_id: str) -> dict[str, Any] | None:
        return await self.db.fetchone("SELECT * FROM sessions WHERE id = ?", (session_id,))


class SignalRepo:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def save(self, signal_id: str, **fields: Any) -> None:
        columns = ", ".join(fields.keys())
        placeholders = ", ".join("?" for _ in fields)
        await self.db.execute(
            f"INSERT INTO signals ({columns}) VALUES ({placeholders})",
            tuple(fields.values()),
        )

    async def mark_delivered(self, signal_id: str) -> None:
        await self.db.execute(
            "UPDATE signals SET delivered_at = ? WHERE id = ?", (_now(), signal_id)
        )


class OutcomeRepo:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def save(self, signal_id: str, result: ResultType, mtg_count: int = 0, review: dict | None = None) -> None:
        await self.db.execute(
            "INSERT INTO outcomes (signal_id, result, mtg_count, review_json, recorded_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (signal_id, result.value, mtg_count, json.dumps(review or {}), _now()),
        )


class StatsRepo:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def record(self, strategy_id: str, pair: str, result: ResultType) -> None:
        column = {
            ResultType.DIRECT_WIN: "wins",
            ResultType.MTG_WIN: "mtg_wins",
            ResultType.BREAK_EVEN: "breakeven",
            ResultType.LOSS: "losses",
            ResultType.MTG_LOSS: "losses",
        }.get(result)
        if column is None:
            return
        await self.db.execute(
            f"""
            INSERT INTO strategy_stats (strategy_id, pair, {column})
            VALUES (?, ?, 1)
            ON CONFLICT(strategy_id, pair)
            DO UPDATE SET {column} = {column} + 1
            """,
            (strategy_id, pair),
        )

    async def get_all(self) -> list[dict[str, Any]]:
        return await self.db.fetchall("SELECT * FROM strategy_stats ORDER BY strategy_id")
