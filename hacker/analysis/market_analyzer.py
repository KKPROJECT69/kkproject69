"""Technical market analysis producing structured evidence for strategies."""
from __future__ import annotations

from dataclasses import dataclass, field

from ..models.candle import Candle


@dataclass
class MarketAnalysis:
    pair: str
    trend: str  # UP / DOWN / SIDEWAYS
    structure: str  # BULLISH / BEARISH / MIXED
    momentum: float  # rate of change %
    rsi: float
    volatility: float  # ATR
    support_levels: list[float]
    resistance_levels: list[float]
    fvg: list[dict]
    breakout_level: float
    breakdown_level: float
    last_close: float
    evidence: dict = field(default_factory=dict)


def _sma(values: list[float], period: int) -> float | None:
    if len(values) < period:
        return None
    return sum(values[-period:]) / period


def _ema(values: list[float], period: int) -> float | None:
    if len(values) < period:
        return None
    multiplier = 2 / (period + 1)
    ema = sum(values[:period]) / period
    for value in values[period:]:
        ema = (value - ema) * multiplier + ema
    return ema


def _rsi(closes: list[float], period: int = 14) -> float:
    if len(closes) < period + 1:
        return 50.0
    gains: list[float] = []
    losses: list[float] = []
    for i in range(1, len(closes)):
        delta = closes[i] - closes[i - 1]
        gains.append(max(delta, 0.0))
        losses.append(max(-delta, 0.0))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - 100 / (1 + rs)


def _atr(candles: list[Candle], period: int = 14) -> float:
    if len(candles) < period + 1:
        return 0.0
    trs: list[float] = []
    for i in range(1, len(candles)):
        c = candles[i]
        p = candles[i - 1]
        trs.append(max(c.high - c.low, abs(c.high - p.close), abs(c.low - p.close)))
    return sum(trs[-period:]) / period


def _swing_points(candles: list[Candle], k: int = 2) -> tuple[list[float], list[float]]:
    highs: list[float] = []
    lows: list[float] = []
    for i in range(k, len(candles) - k):
        window = candles[i - k : i + k + 1]
        if candles[i].high == max(c.high for c in window):
            highs.append(candles[i].high)
        if candles[i].low == min(c.low for c in window):
            lows.append(candles[i].low)
    return highs, lows


def _detect_fvg(candles: list[Candle]) -> list[dict]:
    fvg: list[dict] = []
    for i in range(2, len(candles)):
        if candles[i].low > candles[i - 2].high:
            fvg.append(
                {"type": "bullish", "top": candles[i].low, "bottom": candles[i - 2].high, "index": i}
            )
        elif candles[i].high < candles[i - 2].low:
            fvg.append(
                {"type": "bearish", "top": candles[i - 2].low, "bottom": candles[i].high, "index": i}
            )
    return fvg


def _structure(highs: list[float], lows: list[float]) -> str:
    if len(highs) >= 2 and len(lows) >= 2:
        hh = highs[-1] > highs[-2]
        ll = lows[-1] < lows[-2]
        if hh and not ll:
            return "BULLISH"
        if ll and not hh:
            return "BEARISH"
    return "MIXED"


class MarketAnalyzer:
    """Converts a candle series into structured market evidence."""

    def analyze(self, candles: list[Candle], pair: str) -> MarketAnalysis:
        if not candles:
            return MarketAnalysis(
                pair=pair, trend="SIDEWAYS", structure="MIXED", momentum=0.0, rsi=50.0,
                volatility=0.0, support_levels=[], resistance_levels=[], fvg=[],
                breakout_level=0.0, breakdown_level=0.0, last_close=0.0,
            )

        closes = [c.close for c in candles]
        last_close = closes[-1]

        ema_fast = _ema(closes, 20)
        ema_slow = _ema(closes, 50)
        if ema_fast is not None and ema_slow is not None:
            if ema_fast > ema_slow and last_close > ema_slow:
                trend = "UP"
            elif ema_fast < ema_slow and last_close < ema_slow:
                trend = "DOWN"
            else:
                trend = "SIDEWAYS"
        else:
            trend = "UP" if last_close > closes[0] else "DOWN"

        momentum = (
            (last_close - closes[-10]) / closes[-10] * 100 if len(closes) >= 10 else 0.0
        )
        rsi = _rsi(closes)
        volatility = _atr(candles)
        highs, lows = _swing_points(candles)
        structure = _structure(highs, lows)
        fvg = _detect_fvg(candles)

        support_levels = sorted({round(x, 4) for x in lows[-5:]}) if lows else []
        resistance_levels = sorted({round(x, 4) for x in highs[-5:]}) if highs else []
        breakout_level = max(resistance_levels) if resistance_levels else last_close
        breakdown_level = min(support_levels) if support_levels else last_close

        return MarketAnalysis(
            pair=pair,
            trend=trend,
            structure=structure,
            momentum=round(momentum, 3),
            rsi=round(rsi, 2),
            volatility=round(volatility, 4),
            support_levels=support_levels,
            resistance_levels=resistance_levels,
            fvg=fvg,
            breakout_level=round(breakout_level, 4),
            breakdown_level=round(breakdown_level, 4),
            last_close=round(last_close, 4),
            evidence={
                "ema_fast": round(ema_fast, 4) if ema_fast else None,
                "ema_slow": round(ema_slow, 4) if ema_slow else None,
            },
        )
