"""Backtesting engine — measures real strategy/signal accuracy on history.

Fully local (no AI, no API). Walk-forward: for each candle after a warm-up
window, run analysis + strategies + decision on the candles seen so far, then
resolve the prediction against the *next* candle's close. Produces per-strategy
and overall win/loss statistics.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..analysis.market_analyzer import MarketAnalyzer
from ..decision.engine import SignalDecisionEngine
from ..models.candle import Candle
from ..models.enums import Direction
from ..strategies.aggregator import StrategyAggregator
from ..strategies.registry import StrategyRegistry


@dataclass
class StrategyBacktestStat:
    strategy_id: str
    signals: int = 0
    wins: int = 0
    losses: int = 0

    @property
    def accuracy(self) -> float:
        total = self.wins + self.losses
        return round(self.wins / total * 100, 2) if total else 0.0


@dataclass
class BacktestReport:
    candles_tested: int = 0
    signals: int = 0
    wins: int = 0
    losses: int = 0
    by_strategy: dict[str, StrategyBacktestStat] = field(default_factory=dict)

    @property
    def accuracy(self) -> float:
        total = self.wins + self.losses
        return round(self.wins / total * 100, 2) if total else 0.0


class BacktestEngine:
    def __init__(
        self,
        registry: StrategyRegistry | None = None,
        analyzer: MarketAnalyzer | None = None,
        decision_engine: SignalDecisionEngine | None = None,
        warmup: int = 60,
        min_confidence: float = 70.0,
    ) -> None:
        self.registry = registry or StrategyRegistry()
        self.analyzer = analyzer or MarketAnalyzer()
        self.decision_engine = decision_engine or SignalDecisionEngine(
            StrategyAggregator(), min_confidence=min_confidence
        )
        self.warmup = warmup

    def run(self, candles: list[Candle], pair: str) -> BacktestReport:
        report = BacktestReport(candles_tested=max(0, len(candles) - self.warmup - 1))
        if len(candles) <= self.warmup + 1:
            return report

        for i in range(self.warmup, len(candles) - 1):
            history = candles[: i + 1]
            next_candle = candles[i + 1]
            entry_price = history[-1].close
            exit_price = next_candle.close

            analysis = self.analyzer.analyze(history, pair)
            results = [s.analyze(analysis, history) for s in self.registry.all()]
            decision = self.decision_engine.decide(results, analysis)
            if not decision.approved:
                continue

            report.signals += 1
            win = self._is_win(decision.direction, entry_price, exit_price)
            if win:
                report.wins += 1
            else:
                report.losses += 1

            for r in results:
                if not r.is_directional or r.direction != decision.direction:
                    continue
                stat = report.by_strategy.setdefault(
                    r.strategy_id, StrategyBacktestStat(r.strategy_id)
                )
                stat.signals += 1
                if win:
                    stat.wins += 1
                else:
                    stat.losses += 1
        return report

    @staticmethod
    def _is_win(direction: Direction, entry: float, exit_: float) -> bool:
        if direction == Direction.CALL:
            return exit_ > entry
        if direction == Direction.PUT:
            return exit_ < entry
        return False
