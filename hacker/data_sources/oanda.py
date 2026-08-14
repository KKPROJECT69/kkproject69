"""OANDA live market-data adapter (practice endpoint).

Serves non-OTC forex pairs. OANDA does not provide binary-options payout, so
``get_payout`` returns None. Requires OANDA_API_KEY (and optionally
OANDA_ACCOUNT_ID) in the environment.
"""
from __future__ import annotations

import re
from datetime import datetime

from ..config.settings import get_settings
from ..models.candle import Candle
from ..models.enums import Timeframe
from ..net.http import AsyncHttpClient
from .base import MarketDataSource

_GRANULARITY = {
    Timeframe.M1: "M1",
    Timeframe.M5: "M5",
    Timeframe.M15: "M15",
    Timeframe.M30: "M30",
    Timeframe.H1: "H1",
}


class OandaMarketSource(MarketDataSource):
    name = "oanda"

    def __init__(self, client: AsyncHttpClient | None = None) -> None:
        self.settings = get_settings()
        self._client = client or AsyncHttpClient(proxy=self.settings.market_proxy)

    async def get_candles(
        self, pair: str, timeframe: Timeframe, count: int = 100
    ) -> list[Candle]:
        base = self.settings.oanda_base_url.rstrip("/")
        instrument = normalize_oanda_instrument(pair)
        url = f"{base}/v3/instruments/{instrument}/candles"
        headers = {"Authorization": f"Bearer {self.settings.oanda_api_key}"}
        params = {
            "granularity": _GRANULARITY.get(timeframe, "M1"),
            "count": max(1, min(count, 5000)),
            "price": "M",
        }
        data = await self._client.get_json(url, params=params, headers=headers)
        return self._parse_candles(data)

    @staticmethod
    def _parse_candles(data: dict) -> list[Candle]:
        rows = (data or {}).get("candles") or []
        candles: list[Candle] = []
        for row in rows:
            try:
                mid = row["mid"]
                candles.append(
                    Candle(
                        timestamp=datetime.fromisoformat(row["time"]),
                        open=float(mid["o"]),
                        high=float(mid["h"]),
                        low=float(mid["l"]),
                        close=float(mid["c"]),
                        volume=float(row.get("volume") or 0.0),
                    )
                )
            except (KeyError, TypeError, ValueError):
                continue
        return candles

    async def get_payout(self, pair: str) -> float | None:
        return None


def normalize_oanda_instrument(pair: str) -> str:
    """Normalize a forex pair identifier to OANDA's ``BASE_QUOTE`` form.

    Accepts ``EURUSD``, ``EUR_USD``, ``eur/usd``, ``eurusd`` etc.
    """
    cleaned = re.sub(r"[^A-Za-z]", "", pair).upper()
    if len(cleaned) == 6:
        return f"{cleaned[:3]}_{cleaned[3:]}"
    return cleaned
