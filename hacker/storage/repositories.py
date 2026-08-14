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

    async def list_all(self) -> list[dict[str, Any]]:
        return await self.db.fetchall(
            "SELECT * FROM users ORDER BY created_at DESC"
        )

    async def count(self) -> int:
        row = await self.db.fetchone("SELECT COUNT(*) AS n FROM users")
        return int(row["n"]) if row else 0

    async def set_banned(self, telegram_id: int, banned: bool) -> None:
        await self.db.execute(
            "UPDATE users SET banned = ? WHERE telegram_id = ?",
            (1 if banned else 0, telegram_id),
        )


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
        columns = ["id"] + list(fields.keys())
        placeholders = ", ".join("?" for _ in columns)
        values: list[Any] = [signal_id] + list(fields.values())
        await self.db.execute(
            f"INSERT INTO signals ({', '.join(columns)}) VALUES ({placeholders})",
            tuple(values),
        )

    async def mark_delivered(self, signal_id: str) -> None:
        await self.db.execute(
            "UPDATE signals SET delivered_at = ? WHERE id = ?", (_now(), signal_id)
        )

    async def recent(self, limit: int = 50) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), 500))
        return await self.db.fetchall(
            "SELECT * FROM signals ORDER BY generated_at DESC LIMIT ?", (limit,)
        )

    async def count(self) -> int:
        row = await self.db.fetchone("SELECT COUNT(*) AS n FROM signals")
        return int(row["n"]) if row else 0

    async def count_delivered(self) -> int:
        row = await self.db.fetchone(
            "SELECT COUNT(*) AS n FROM signals WHERE delivered_at IS NOT NULL"
        )
        return int(row["n"]) if row else 0


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

    async def summary(self) -> dict[str, Any]:
        rows = await self.get_all()
        wins = sum((r["wins"] or 0) + (r["mtg_wins"] or 0) for r in rows)
        losses = sum(r["losses"] or 0 for r in rows)
        breakeven = sum(r["breakeven"] or 0 for r in rows)
        total = wins + losses + breakeven
        return {
            "total": total,
            "wins": wins,
            "losses": losses,
            "breakeven": breakeven,
            "accuracy": round(wins / total * 100, 2) if total else 0.0,
            "by_strategy": [
                {
                    "strategy_id": r["strategy_id"],
                    "pair": r["pair"],
                    "wins": r["wins"] or 0,
                    "mtg_wins": r["mtg_wins"] or 0,
                    "losses": r["losses"] or 0,
                    "breakeven": r["breakeven"] or 0,
                }
                for r in rows
            ],
        }


class OutcomeRepoSummary:
    """Helpers for the outcome table (counts + totals)."""

    def __init__(self, db: Database) -> None:
        self.db = db

    async def summary(self) -> dict[str, Any]:
        row = await self.db.fetchone(
            """
            SELECT COUNT(*) AS total,
                   SUM(CASE WHEN result IN ('DIRECT_WIN','MTG_WIN') THEN 1 ELSE 0 END) AS wins,
                   SUM(CASE WHEN result IN ('LOSS','MTG_LOSS') THEN 1 ELSE 0 END) AS losses,
                   SUM(CASE WHEN result = 'BREAK_EVEN' THEN 1 ELSE 0 END) AS breakeven
            FROM outcomes
            """
        )
        total = int(row["total"] or 0) if row else 0
        wins = int(row["wins"] or 0) if row else 0
        return {
            "total": total,
            "wins": wins,
            "losses": int(row["losses"] or 0) if row else 0,
            "breakeven": int(row["breakeven"] or 0) if row else 0,
            "accuracy": round(wins / total * 100, 2) if total else 0.0,
        }


class SettingsRepo:
    """Persistent runtime settings overrides (key/value)."""

    def __init__(self, db: Database) -> None:
        self.db = db

    async def get(self, key: str, default: str | None = None) -> str | None:
        row = await self.db.fetchone(
            "SELECT value FROM app_settings WHERE key = ?", (key,)
        )
        return row["value"] if row else default

    async def set(self, key: str, value: str) -> None:
        await self.db.execute(
            """
            INSERT INTO app_settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, value),
        )

    async def all(self) -> dict[str, str]:
        rows = await self.db.fetchall("SELECT * FROM app_settings ORDER BY key")
        return {r["key"]: r["value"] for r in rows}


class AuditRepo:
    """Append-only audit log for admin actions."""

    def __init__(self, db: Database) -> None:
        self.db = db

    async def log(self, actor: str, action: str, detail: str = "") -> None:
        await self.db.execute(
            "INSERT INTO audit_log (actor, action, detail, created_at) VALUES (?, ?, ?, ?)",
            (actor, action, detail, _now()),
        )

    async def recent(self, limit: int = 50) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), 500))
        return await self.db.fetchall(
            "SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,)
        )
