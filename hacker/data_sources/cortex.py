"""Cortex/Quotex OTC candle-data adapter — placeholder stub.

TODO: the project history mentions a Cortex/Quotex-related OTC data
requirement. Only a *data* API should be used here — never an execution API.
Inherits the mock source until a real candle endpoint is wired.
"""
from __future__ import annotations

from .mock import MockMarketSource


class CortexMarketSource(MockMarketSource):
    name = "cortex"
