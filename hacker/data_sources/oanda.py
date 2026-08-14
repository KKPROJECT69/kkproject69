"""OANDA live market-data adapter — placeholder stub.

TODO: implement against OANDA's candle endpoint when configured. For now it
inherits the mock source so the pipeline remains runnable; swap in a real
implementation when OANDA credentials/URL are provided.
"""
from __future__ import annotations

from .mock import MockMarketSource


class OandaMarketSource(MockMarketSource):
    name = "oanda"
