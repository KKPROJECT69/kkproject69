from hacker.analysis.market_analyzer import MarketAnalyzer
from hacker.data_sources.mock import MockMarketSource
from hacker.decision.engine import SignalDecisionEngine
from hacker.filters import MarketFilterEngine, NewsFilter, PayoutFilter
from hacker.models.enums import Timeframe
from hacker.pipeline import SignalPipeline
from hacker.strategies.aggregator import StrategyAggregator
from hacker.strategies.registry import StrategyRegistry
from hacker.timing.engine import SignalTimingEngine


def _pipeline() -> SignalPipeline:
    return SignalPipeline(
        source=MockMarketSource(seed=7),
        analyzer=MarketAnalyzer(),
        registry=StrategyRegistry(),
        decision_engine=SignalDecisionEngine(StrategyAggregator(), min_confidence=70.0),
        payout_filter=PayoutFilter(0.0),
        news_filter=NewsFilter(),
        market_filters=MarketFilterEngine(),
        timing=SignalTimingEngine(17.0),
    )


async def test_pipeline_runs_end_to_end():
    pipeline = _pipeline()
    result = await pipeline.generate("USDBDT_otc", Timeframe.M1)
    # Pipeline must not raise; result is either an approved signal or NO_TRADE (None).
    assert result is None or result.direction.value in ("CALL", "PUT")
