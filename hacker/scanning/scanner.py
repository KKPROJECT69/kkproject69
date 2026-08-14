"""Pair scanner — payout ranking + best-setup discovery across OTC pairs.

Fully local (no AI). Scans a list of OTC pairs, fetches each pair's payout,
ranks by payout, and optionally runs the full pipeline on the top pairs to
surface the strongest current setup.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..data_sources.base import MarketDataSource
from ..models.enums import Timeframe
from ..models.signal import FinalSignal
from ..pipeline import SignalPipeline

DEFAULT_OTC_PAIRS = [
    "EURUSD-OTC", "GBPUSD-OTC", "USDJPY-OTC", "AUDUSD-OTC", "USDCAD-OTC",
    "USDCHF-OTC", "EURGBP-OTC", "BTCUSD-OTC", "USDBDT-OTC", "USDPKR-OTC",
]


@dataclass
class PairPayout:
    pair: str
    payout: float | None


class PairScanner:
    def __init__(self, source: MarketDataSource) -> None:
        self.source = source

    async def payout_ranking(
        self, pairs: list[str] | None = None
    ) -> list[PairPayout]:
        pairs = pairs or DEFAULT_OTC_PAIRS
        results: list[PairPayout] = []
        for pair in pairs:
            payout = await self.source.get_payout(pair)
            results.append(PairPayout(pair, payout))
        return sorted(
            results,
            key=lambda p: p.payout if p.payout is not None else -1.0,
            reverse=True,
        )

    async def best_setups(
        self,
        pairs: list[str] | None = None,
        timeframe: Timeframe = Timeframe.M1,
        pipeline: SignalPipeline | None = None,
        top_n: int = 5,
    ) -> list[FinalSignal]:
        """Run the full pipeline on top-payout pairs and return approved signals."""
        pairs = pairs or DEFAULT_OTC_PAIRS
        ranking = await self.payout_ranking(pairs)
        top = [p.pair for p in ranking[:top_n]]
        signals: list[FinalSignal] = []
        if pipeline is None:
            return signals
        for pair in top:
            signal = await pipeline.generate(pair, timeframe)
            if signal is not None:
                signals.append(signal)
        return signals
