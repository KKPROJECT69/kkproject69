"""Central signal pipeline wiring every stage together.

market → analyze → 11 strategies → AI decision → filters → timing → dispatch
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol
from uuid import uuid4

from .analysis.confluence import ConfluenceChecker
from .analysis.market_analyzer import MarketAnalyzer
from .analysis.regime import RegimeDetector
from .data_sources.base import MarketDataSource
from .decision.engine import SignalDecisionEngine
from .filters.market_filters import MarketFilterEngine
from .filters.news_filter import NewsFilter
from .filters.payout_filter import PayoutFilter
from .models.enums import Direction, Regime, RiskLevel, Timeframe
from .models.signal import FinalSignal
from .strategies.registry import StrategyRegistry
from .timing.engine import SignalTimingEngine


class SignalSink(Protocol):
    async def dispatch(self, signal: FinalSignal) -> None: ...


class SignalPipeline:
    def __init__(
        self,
        source: MarketDataSource,
        analyzer: MarketAnalyzer,
        registry: StrategyRegistry,
        decision_engine: SignalDecisionEngine,
        payout_filter: PayoutFilter,
        news_filter: NewsFilter,
        market_filters: MarketFilterEngine,
        timing: SignalTimingEngine,
        dispatcher: SignalSink | None = None,
        confluence: ConfluenceChecker | None = None,
        regime_detector: RegimeDetector | None = None,
        require_confluence: bool = False,
        avoid_volatile: bool = False,
    ) -> None:
        self.source = source
        self.analyzer = analyzer
        self.registry = registry
        self.decision_engine = decision_engine
        self.payout_filter = payout_filter
        self.news_filter = news_filter
        self.market_filters = market_filters
        self.timing = timing
        self.dispatcher = dispatcher
        self.confluence = confluence
        self.regime_detector = regime_detector
        self.require_confluence = require_confluence
        self.avoid_volatile = avoid_volatile

    async def generate(
        self,
        pair: str,
        timeframe: Timeframe,
        strategy_ids: list[str] | None = None,
        context: dict | None = None,
        user_id: int | None = None,
        session_id: str | None = None,
        min_payout: float | None = None,
        skip_news: bool = False,
    ) -> FinalSignal | None:
        context = context or {}

        candles = await self.source.get_candles(pair, timeframe, count=200)
        if not candles:
            return None  # fail-safe NO_TRADE

        analysis = self.analyzer.analyze(candles, pair)
        strategies = self.registry.select(strategy_ids)
        results = [s.analyze(analysis, candles) for s in strategies]
        decision = await self.decision_engine.decide_async(results, analysis, context)
        if not decision.approved:
            return None

        # Regime filter: skip signals in a volatile (news-like) market.
        if self.avoid_volatile and self.regime_detector is not None:
            if self.regime_detector.detect(analysis) == Regime.VOLATILE:
                return None

        # Multi-timeframe confluence: require higher timeframes to agree.
        if self.require_confluence and self.confluence is not None:
            conf = await self.confluence.check(
                pair, timeframe, base_direction=decision.direction
            )
            if conf.direction != decision.direction:
                return None

        target = self.timing.target_candle_start(timeframe)

        payout = await self.source.get_payout(pair)
        effective_min = min_payout if min_payout is not None else self.payout_filter.min_payout
        if payout is not None and effective_min > 0 and payout < effective_min:
            return None

        if not skip_news:
            ok, _reason = self.news_filter.check(context.get("news_events", []), target)
            if not ok:
                return None

        ok, _reasons = self.market_filters.apply(pair)
        if not ok:
            return None

        if self.timing.is_stale(target):
            return None
        if self.timing.already_sent(pair, target):
            return None
        self.timing.mark_sent(pair, target)

        risk_level = _extract_risk_level(results)
        signal = FinalSignal(
            signal_id=uuid4().hex[:12],
            pair=pair,
            direction=decision.direction,
            timeframe=timeframe,
            target_entry=target,
            confidence=decision.confidence,
            payout=payout,
            strategy=", ".join(decision.supporting_strategies),
            reason=decision.reasoning,
            ai_verdict=decision.verdict,
            risk_level=risk_level,
            session_id=session_id,
            user_id=user_id,
            generated_at=datetime.now(timezone.utc),
        )
        if self.dispatcher is not None:
            await self.dispatcher.dispatch(signal)
        return signal


def _extract_risk_level(results: list) -> str:
    for r in results:
        if r.strategy_id == "risk_control" and r.evidence.get("risk_level"):
            return str(r.evidence["risk_level"])
    return RiskLevel.MEDIUM.value
