"""Forex Factory weekly JSON calendar adapter (free, no API key)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ..config.settings import get_settings
from ..models.enums import Impact
from ..net.http import AsyncHttpClient


@dataclass
class EconomicEvent:
    title: str
    country: str
    currency: str
    date: datetime
    impact: Impact
    forecast: str = ""
    previous: str = ""


class ForexFactoryCalendar:
    def __init__(self, client: AsyncHttpClient | None = None) -> None:
        self.settings = get_settings()
        self._client = client or AsyncHttpClient(proxy=self.settings.market_proxy)

    async def fetch_week(self) -> list[EconomicEvent]:
        url = self.settings.forex_factory_url
        if not url:
            return []
        try:
            data = await self._client.get_json(url)
            return self._parse(data)
        except Exception:
            return []

    @staticmethod
    def _parse(data: Any) -> list[EconomicEvent]:
        rows = data if isinstance(data, list) else []
        events: list[EconomicEvent] = []
        for item in rows:
            try:
                raw_date = str(item.get("date", ""))
                if raw_date.endswith("Z"):
                    raw_date = raw_date[:-1] + "+00:00"
                impact_raw = str(item.get("impact") or "Low").capitalize()
                impact = Impact(impact_raw) if impact_raw in {i.value for i in Impact} else Impact.LOW
                events.append(
                    EconomicEvent(
                        title=str(item.get("title") or ""),
                        country=str(item.get("country") or ""),
                        currency=str(item.get("currency") or ""),
                        date=datetime.fromisoformat(raw_date),
                        impact=impact,
                        forecast=str(item.get("forecast") or ""),
                        previous=str(item.get("previous") or ""),
                    )
                )
            except (KeyError, TypeError, ValueError):
                continue
        return events
