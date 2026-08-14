"""SQLite persistence layer (async via aiosqlite)."""
from __future__ import annotations

import os
from typing import Any

import aiosqlite

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    telegram_id  INTEGER PRIMARY KEY,
    username     TEXT,
    access_level TEXT NOT NULL DEFAULT 'FREE',
    settings_json TEXT,
    created_at   TEXT
);

CREATE TABLE IF NOT EXISTS sessions (
    id          TEXT PRIMARY KEY,
    user_id     INTEGER NOT NULL,
    type        TEXT NOT NULL,
    strategy_id TEXT,
    pairs       TEXT,
    status      TEXT NOT NULL DEFAULT 'IDLE',
    started_at  TEXT,
    ended_at    TEXT
);

CREATE TABLE IF NOT EXISTS signals (
    id            TEXT PRIMARY KEY,
    session_id    TEXT,
    user_id       INTEGER,
    pair          TEXT NOT NULL,
    direction     TEXT NOT NULL,
    timeframe     TEXT NOT NULL,
    entry_time    TEXT NOT NULL,
    target_candle TEXT,
    payout        REAL,
    confidence    REAL,
    strategy      TEXT,
    reason        TEXT,
    ai_verdict    TEXT,
    risk_level    TEXT,
    generated_at  TEXT,
    delivered_at  TEXT,
    status        TEXT DEFAULT 'PENDING'
);

CREATE TABLE IF NOT EXISTS outcomes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    signal_id   TEXT NOT NULL,
    result      TEXT NOT NULL,
    mtg_count   INTEGER DEFAULT 0,
    review_json TEXT,
    recorded_at TEXT
);

CREATE TABLE IF NOT EXISTS strategy_stats (
    strategy_id TEXT NOT NULL,
    pair        TEXT NOT NULL,
    wins        INTEGER DEFAULT 0,
    losses      INTEGER DEFAULT 0,
    breakeven   INTEGER DEFAULT 0,
    mtg_wins    INTEGER DEFAULT 0,
    PRIMARY KEY (strategy_id, pair)
);

CREATE TABLE IF NOT EXISTS paper_trades (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER,
    pair        TEXT,
    direction   TEXT,
    stake       REAL,
    entry_price REAL,
    status      TEXT,
    result      TEXT,
    created_at  TEXT
);
"""


class Database:
    def __init__(self, path: str) -> None:
        self.path = path
        self._conn: aiosqlite.Connection | None = None

    async def connect(self) -> aiosqlite.Connection:
        if self._conn is None:
            directory = os.path.dirname(self.path)
            if directory:
                os.makedirs(directory, exist_ok=True)
            self._conn = await aiosqlite.connect(self.path)
            self._conn.row_factory = aiosqlite.Row
            await self._conn.executescript(SCHEMA)
            await self._conn.commit()
        return self._conn

    async def execute(self, sql: str, params: tuple = ()) -> aiosqlite.Cursor:
        conn = await self.connect()
        cursor = await conn.execute(sql, params)
        await conn.commit()
        return cursor

    async def fetchall(self, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
        conn = await self.connect()
        cursor = await conn.execute(sql, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def fetchone(self, sql: str, params: tuple = ()) -> dict[str, Any] | None:
        rows = await self.fetchall(sql, params)
        return rows[0] if rows else None

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None
