"""Shared async HTTP client with proxy + retry support.

Every outbound network call (market data, news, Telegram) should go through
this class so that proxy routing stays configurable and independent per route.
"""
from __future__ import annotations

import asyncio
from typing import Any, Self

import httpx


class AsyncHttpClient:
    def __init__(
        self,
        proxy: str | None = None,
        timeout: float = 15.0,
        retries: int = 3,
    ) -> None:
        self.proxy = proxy
        self.timeout = timeout
        self.retries = retries
        self._client: httpx.AsyncClient | None = None

    async def start(self) -> httpx.AsyncClient:
        if self._client is None:
            transport = None
            if self.proxy:
                transport = httpx.AsyncHTTPTransport(proxy=self.proxy)
            self._client = httpx.AsyncClient(timeout=self.timeout, transport=transport)
        return self._client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def get_json(
        self,
        url: str,
        params: dict | None = None,
        headers: dict | None = None,
    ) -> Any:
        client = await self.start()
        last_exc: Exception | None = None
        for attempt in range(self.retries):
            try:
                resp = await client.get(url, params=params, headers=headers)
                resp.raise_for_status()
                return resp.json()
            except (httpx.HTTPError, ValueError) as exc:
                last_exc = exc
                await asyncio.sleep(1.0 * (attempt + 1))
        raise last_exc  # type: ignore[misc]

    async def __aenter__(self) -> Self:
        await self.start()
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()
