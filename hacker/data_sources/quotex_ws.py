"""Quotex live tick WebSocket stream (optional, for live ticks / charting).

Streams real-time ``{type, symbol, timestamp, price}`` frames. Requires the
``websockets`` package. Keep market-data REST traffic on its own route; this
module is only for live tick consumers (future live chart / OTC tick display).
"""
from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator

from ..config.settings import get_settings

log = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency
    import websockets
except ImportError:  # pragma: no cover
    websockets = None

HEARTBEAT_INTERVAL = 25.0


class QuotexTickStream:
    def __init__(self, ws_url: str | None = None) -> None:
        self.settings = get_settings()
        self.ws_url = (ws_url or self.settings.quotex_ws_url).rstrip("/")
        self._ws = None

    async def stream(self, symbols: list[str]) -> AsyncIterator[dict]:
        """Connect, subscribe, and yield tick dicts until cancelled.

        Reconnects with capped exponential backoff; sends heartbeats so idle
        connections are not closed by the edge.
        """
        if websockets is None:
            raise RuntimeError("websockets package is required for the tick stream")
        retry = 0
        while True:
            try:
                async with websockets.connect(
                    f"{self.ws_url}?symbols={','.join(symbols)}"
                ) as ws:
                    self._ws = ws
                    retry = 0
                    heartbeat = asyncio.create_task(self._heartbeat(ws))
                    try:
                        async for raw in ws:
                            try:
                                msg = json.loads(raw)
                            except json.JSONDecodeError:
                                continue
                            if msg.get("type") == "tick":
                                yield msg
                    finally:
                        heartbeat.cancel()
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001
                retry += 1
                delay = min(1.0 * (2 ** (retry - 1)), 15.0)
                log.warning("Quotex tick stream error (%s); retrying in %.1fs", exc, delay)
                await asyncio.sleep(delay)

    async def _heartbeat(self, ws) -> None:  # pragma: no cover - trivial loop
        while True:
            await asyncio.sleep(HEARTBEAT_INTERVAL)
            await ws.send(json.dumps({"action": "ping"}))
