"""Market regime detection — classifies the current market state.

Fully local (no AI, no API). Regimes:
- TREND_UP / TREND_DOWN — directional, trending market
- RANGING — low volatility, sideways
- VOLATILE — high volatility (news / fast market)
"""
from __future__ import annotations

from ..models.enums import Regime
from .market_analyzer import MarketAnalysis

_VOLATILE_RATIO = 0.015  # ATR / price above this = volatile
_RANGING_RATIO = 0.003   # ATR / price below this = ranging


class RegimeDetector:
    def __init__(
        self,
        volatile_ratio: float = _VOLATILE_RATIO,
        ranging_ratio: float = _RANGING_RATIO,
    ) -> None:
        self.volatile_ratio = volatile_ratio
        self.ranging_ratio = ranging_ratio

    def detect(self, analysis: MarketAnalysis) -> Regime:
        if analysis.last_close <= 0:
            return Regime.RANGING
        ratio = analysis.volatility / analysis.last_close
        if ratio >= self.volatile_ratio:
            return Regime.VOLATILE
        if analysis.trend == "UP":
            return Regime.TREND_UP
        if analysis.trend == "DOWN":
            return Regime.TREND_DOWN
        if ratio <= self.ranging_ratio:
            return Regime.RANGING
        return Regime.RANGING
