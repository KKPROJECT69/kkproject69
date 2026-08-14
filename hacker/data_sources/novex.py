"""NovexAI payout source.

The Quotex proxy provides live candle data but no payout. NovexAI's
``api.php`` returns the latest candle(s) including a ``payout`` field, which
is the OTC payout source.
"""
from __future__ import annotations

from ..config.settings import get_settings
from ..net.http import AsyncHttpClient


class NovexPayoutSource:
    name = "novex_payout"

    def __init__(self, client: AsyncHttpClient | None = None) -> None:
        self.settings = get_settings()
        self._client = client or AsyncHttpClient(proxy=self.settings.market_proxy)

    async def get_payout(self, pair: str) -> float | None:
        """Return current payout % for an OTC pair, or None on failure."""
        url = self.settings.novex_payout_url.rstrip("/")
        if not url:
            return None
        params = {"pair": _to_novex_pair(pair), "count": 1}
        try:
            data = await self._client.get_json(url, params=params)
        except Exception:
            return None
        rows = data.get("data") if isinstance(data, dict) else None
        if not rows:
            return None
        payout = rows[0].get("payout")
        try:
            return float(payout)
        except (TypeError, ValueError):
            return None


def _to_novex_pair(pair: str) -> str:
    """Normalize any OTC pair identifier to NovexAI's ``BASEQUOTE_otc`` form."""
    base = _strip_otc(pair)
    return f"{base}_otc"


def _strip_otc(pair: str) -> str:
    text = "".join(ch for ch in pair.upper() if ch.isalnum())
    if text.endswith("OTC"):
        text = text[: -len("OTC")]
    return text
