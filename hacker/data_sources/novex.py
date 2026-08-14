"""NovexAI market-data adapter (current tested OTC source).

The upstream response schema should be confirmed against the live endpoint;
the parser below accepts the most common shapes (a bare list, or an object
with "candles"/"data"), mapping time/open/high/low/close/volume/payout.
On any error or missing config it falls back to the mock source so the rest
of the pipeline stays runnable.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ..config.settings import get_settings
from ..models.candle import Candle
from ..models.enums import Timeframe
from ..net.http import AsyncHttpClient
from .base import MarketDataSource
from .mock import MockMarketSource


class NovexMarketSource(MarketDataSource):
    name = "novex"

    def __init__(
        self,
        client: AsyncHttpClient | None = None,
        fallback: MarketDataSource | None = None,
    ) -> None:
        self.settings = get_settings()
        self._client = client or AsyncHttpClient(proxy=self.settings.market_proxy)
        self._fallback = fallback or MockMarketSource()

    async def get_candles(
        self, pair: str, timeframe: Timeframe, count: int = 100
    ) -> list[Candle]:
        base = self.settings.novex_base_url.rstrip("/")
        if not base:
            return await self._fallback.get_candles(pair, timeframe, count)

        url = f"{base}/candles"
        params = {"symbol": pair, "timeframe": timeframe.value, "limit": count}
        headers = (
            {"Authorization": f"Bearer {self.settings.novex_api_key}"}
            if self.settings.novex_api_key
            else {}
        )
        try:
            data = await self._client.get_json(url, params=params, headers=headers)
            candles = self._parse_candles(data)
            if candles:
                return candles
        except Exception:
            pass
        return await self._fallback.get_candles(pair, timeframe, count)

    @staticmethod
    def _parse_candles(data: Any) -> list[Candle]:
        rows = data if isinstance(data, list) else (data or {}).get("candles") or (data or {}).get("data") or []
        candles: list[Candle] = []
        for row in rows:
            try:
                ts_raw = (
                    row.get("time")
                    or row.get("timestamp")
                    or row.get("t")
                    or row.get("open_time")
                    or row.get("datetime")
                )
                ts = _to_datetime(ts_raw)
                o = float(row.get("open") or row.get("o"))
                h = float(row.get("high") or row.get("h"))
                l = float(row.get("low") or row.get("l"))
                c = float(row.get("close") or row.get("c"))
                volume = float(row.get("volume") or row.get("v") or 0.0)
                payout = row.get("payout")
                candles.append(
                    Candle(
                        timestamp=ts,
                        open=o,
                        high=h,
                        low=l,
                        close=c,
                        volume=volume,
                        payout=float(payout) if payout is not None else None,
                    )
                )
            except (KeyError, TypeError, ValueError):
                continue
        return candles

    async def get_payout(self, pair: str) -> float | None:
        candles = await self.get_candles(pair, Timeframe.M1, count=1)
        return candles[-1].payout if candles else None


def _to_datetime(raw: Any) -> datetime:
    if isinstance(raw, datetime):
        return raw
    if isinstance(raw, (int, float)):
        return datetime.fromtimestamp(raw, tz=timezone.utc)
    text = str(raw)
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    return datetime.fromisoformat(text)
