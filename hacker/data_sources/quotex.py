"""Quotex Live Tick API adapter (quotex-proxy-pal.lovable.app).

Provides live OTC candle data via the REST fallback endpoint and live tick
streaming via WebSocket. Symbol convention is ``BASEQUOTE-OTC`` (e.g.
``USDBDT-OTC``); timestamps are unix epoch (seconds for REST candles,
milliseconds for WS ticks) in UTC. No payout is available here.
"""
from __future__ import annotations

from datetime import UTC, datetime

from ..config.settings import get_settings
from ..models.candle import Candle
from ..models.enums import Timeframe
from ..net.http import AsyncHttpClient
from .base import MarketDataSource


class QuotexProxySource(MarketDataSource):
    name = "quotex"

    def __init__(self, client: AsyncHttpClient | None = None) -> None:
        self.settings = get_settings()
        self._client = client or AsyncHttpClient(proxy=self.settings.market_proxy)

    async def get_candles(
        self, pair: str, timeframe: Timeframe, count: int = 100
    ) -> list[Candle]:
        base = self.settings.quotex_base_url.rstrip("/")
        url = f"{base}/candles"
        params = {
            "symbol": to_quotex_symbol(pair),
            "interval": timeframe.value,
            "limit": max(1, min(count, 600)),
        }
        data = await self._client.get_json(url, params=params)
        return self._parse_candles(data)

    @staticmethod
    def _parse_candles(data: dict) -> list[Candle]:
        inner = (data or {}).get("candles") or {}
        rows = inner.get("candles") or []
        candles: list[Candle] = []
        for row in rows:
            try:
                ts = row["time"]
                candles.append(
                    Candle(
                        timestamp=datetime.fromtimestamp(ts, tz=UTC),
                        open=float(row["open"]),
                        high=float(row["high"]),
                        low=float(row["low"]),
                        close=float(row["close"]),
                        volume=float(row.get("volume") or 0.0),
                    )
                )
            except (KeyError, TypeError, ValueError):
                continue
        return candles

    async def get_payout(self, pair: str) -> float | None:
        return None  # payout is served by NovexPayoutSource


def to_quotex_symbol(pair: str) -> str:
    """Normalize any OTC pair identifier to Quotex ``BASEQUOTE-OTC`` form."""
    text = "".join(ch for ch in pair.upper() if ch.isalnum())
    text = text.removesuffix("OTC")
    return f"{text}-OTC"
