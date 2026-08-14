"""News filter — avoid signals around high-impact economic events."""
from __future__ import annotations

from datetime import datetime, timedelta

from ..calendar.forex_factory import EconomicEvent
from ..models.enums import Impact


class NewsFilter:
    def __init__(self, window_minutes: int = 15) -> None:
        self.window_minutes = window_minutes

    def check(
        self, events: list[EconomicEvent], entry_time: datetime
    ) -> tuple[bool, str]:
        if not events:
            return True, "no news data"
        window = timedelta(minutes=self.window_minutes)
        for event in events:
            if event.impact != Impact.HIGH:
                continue
            try:
                delta = abs(event.date - entry_time)
            except TypeError:
                # naive vs aware datetime — compare naively
                delta = abs(event.date.replace(tzinfo=None) - entry_time.replace(tzinfo=None))
            if delta <= window:
                return False, f"high-impact event '{event.title}' near entry time"
        return True, "no high-impact news in window"
