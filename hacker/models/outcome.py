"""Trade-outcome dataclass."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from .enums import ResultType


@dataclass
class Outcome:
    signal_id: str
    result: ResultType = ResultType.PENDING
    mtg_count: int = 0
    review: dict = field(default_factory=dict)
    recorded_at: datetime | None = None
