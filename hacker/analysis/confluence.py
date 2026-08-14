"""Multi-timeframe confluence — higher-timeframe trend agreement.

Fully local. A base-timeframe signal is stronger when the higher timeframes
agree. This checker fetches candles for multiple timeframes and returns a
confluence score/direction used to confirm or reject a base setup.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..data_sources.base import MarketDataSource
from ..models.enums import Direction, Timeframe
from .market_analyzer import MarketAnalysis, MarketAnalyzer


@dataclass
class ConfluenceResult:
    direction: Direction  # agreed direction, or NO_TRADE
    score: float          # 0..1 fraction of higher timeframes agreeing
    details: list[str]


class ConfluenceChecker:
    def __init__(
        self,
        source: MarketDataSource,
        analyzer: MarketAnalyzer | None = None,
    ) -> None:
        self.source = source
        self.analyzer = analyzer or MarketAnalyzer()

    async def check(
        self,
        pair: str,
        base_timeframe: Timeframe,
        higher_timeframes: list[Timeframe] | None = None,
        base_direction: Direction | None = None,
    ) -> ConfluenceResult:
        higher = higher_timeframes or self._defaults(base_timeframe)
        trends: list[str] = []
        details: list[str] = []
        for tf in higher:
            candles = await self.source.get_candles(pair, tf, count=200)
            if not candles:
                details.append(f"{tf.value}: no data")
                continue
            analysis = self.analyzer.analyze(candles, pair)
            details.append(f"{tf.value}: {analysis.trend} ({analysis.structure})")
            trends.append(analysis.trend)

        if not trends:
            return ConfluenceResult(Direction.NO_TRADE, 0.0, details)

        ups = trends.count("UP")
        downs = trends.count("DOWN")
        total = len(trends)
        if base_direction == Direction.CALL:
            score = ups / total
            direction = Direction.CALL if ups >= downs else Direction.NO_TRADE
        elif base_direction == Direction.PUT:
            score = downs / total
            direction = Direction.PUT if downs >= ups else Direction.NO_TRADE
        else:
            # infer the base direction from higher-timeframe majority
            if ups > downs:
                direction, score = Direction.CALL, ups / total
            elif downs > ups:
                direction, score = Direction.PUT, downs / total
            else:
                direction, score = Direction.NO_TRADE, 0.0
        return ConfluenceResult(direction, round(score, 2), details)

    @staticmethod
    def _defaults(base: Timeframe) -> list[Timeframe]:
        return {
            Timeframe.M1: [Timeframe.M5, Timeframe.M15],
            Timeframe.M5: [Timeframe.M15, Timeframe.H1],
            Timeframe.M15: [Timeframe.M30, Timeframe.H1],
            Timeframe.M30: [Timeframe.H1],
            Timeframe.H1: [],
        }.get(base, [Timeframe.M5])
