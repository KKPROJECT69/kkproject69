"""Signal timing engine — 15–20s pre-candle delivery, stale & duplicate guards."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from ..models.enums import Timeframe


class SignalTimingEngine:
    def __init__(self, lead_seconds: float = 17.0) -> None:
        self.lead_seconds = lead_seconds
        self._sent: set[tuple[str, datetime]] = set()

    def target_candle_start(
        self, timeframe: Timeframe, when: datetime | None = None
    ) -> datetime:
        """Return the UTC start of the next candle boundary for `timeframe`."""
        when = when or datetime.now(timezone.utc)
        seconds = timeframe.seconds
        epoch = int(when.timestamp())
        next_boundary = (epoch // seconds + 1) * seconds
        return datetime.fromtimestamp(next_boundary, tz=timezone.utc)

    def send_at(self, target_entry: datetime) -> datetime:
        return target_entry - timedelta(seconds=self.lead_seconds)

    def is_stale(self, target_entry: datetime, when: datetime | None = None) -> bool:
        when = when or datetime.now(timezone.utc)
        return self.send_at(target_entry) <= when

    def already_sent(self, pair: str, target_entry: datetime) -> bool:
        return (pair, target_entry) in self._sent

    def mark_sent(self, pair: str, target_entry: datetime) -> None:
        self._sent.add((pair, target_entry))

    def clear(self) -> None:
        self._sent.clear()
