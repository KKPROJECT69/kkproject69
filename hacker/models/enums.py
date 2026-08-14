"""Core enums shared across the system."""
from __future__ import annotations

from enum import Enum


class Direction(str, Enum):
    CALL = "CALL"
    PUT = "PUT"
    NO_TRADE = "NO_TRADE"


class Timeframe(str, Enum):
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"

    @property
    def seconds(self) -> int:
        return {
            Timeframe.M1: 60,
            Timeframe.M5: 300,
            Timeframe.M15: 900,
            Timeframe.M30: 1800,
            Timeframe.H1: 3600,
        }[self]


class AccessLevel(str, Enum):
    FREE = "FREE"
    PREMIUM = "PREMIUM"
    VIP = "VIP"
    ADMIN = "ADMIN"


class SessionType(str, Enum):
    COMBINED = "COMBINED"
    SINGLE = "SINGLE"
    OTC = "OTC"
    PAPER = "PAPER"


class SessionStatus(str, Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"


class ResultType(str, Enum):
    PENDING = "PENDING"
    DIRECT_WIN = "DIRECT_WIN"
    MTG_WIN = "MTG_WIN"
    MTG_LOSS = "MTG_LOSS"
    BREAK_EVEN = "BREAK_EVEN"
    LOSS = "LOSS"


class Impact(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
