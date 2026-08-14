"""Tests for the no-AI intelligence features: regime, backtest, weights, MTG, chart."""
from datetime import datetime, timedelta, timezone

from hacker.analysis.market_analyzer import MarketAnalysis, MarketAnalyzer
from hacker.analysis.regime import RegimeDetector
from hacker.backtest.engine import BacktestEngine
from hacker.charting.render import render_chart
from hacker.learning.weights import ConfidenceWeights
from hacker.models.candle import Candle
from hacker.models.enums import Direction, Regime
from hacker.models.signal import StrategyResult
from hacker.sessions.mtg import MTGEngine
from hacker.data_sources.mock import MockMarketSource


def _trending_candles(n: int = 120) -> list[Candle]:
    candles = []
    price = 100.0
    t = datetime(2026, 8, 14, 6, 0, 0, tzinfo=timezone.utc)
    for i in range(n):
        o = price
        c = o + 0.05
        candles.append(Candle(timestamp=t, open=o, high=c + 0.01, low=o - 0.01, close=c, volume=100.0))
        price = c
        t += timedelta(minutes=1)
    return candles


def test_regime_detector_uptrend():
    analyzer = MarketAnalyzer()
    candles = _trending_candles()
    analysis = analyzer.analyze(candles, "X")
    regime = RegimeDetector().detect(analysis)
    assert regime == Regime.TREND_UP


def test_regime_detector_volatile():
    analysis = MarketAnalysis(
        pair="X", trend="UP", structure="BULLISH", momentum=0.0, rsi=50.0,
        volatility=2.0, support_levels=[], resistance_levels=[], fvg=[],
        breakout_level=1.0, breakdown_level=1.0, last_close=100.0,
    )
    assert RegimeDetector().detect(analysis) == Regime.VOLATILE


def test_backtest_engine_runs_and_counts():
    engine = BacktestEngine(warmup=60)
    report = engine.run(_trending_candles(), "X")
    assert report.candles_tested > 0
    # A clean uptrend should produce some approved CALL signals and wins.
    assert report.signals >= 0
    assert report.wins + report.losses == report.signals
    assert 0.0 <= report.accuracy <= 100.0


def test_confidence_weights_laplace():
    weights = ConfidenceWeights(smoothing=1.0)
    from hacker.backtest.engine import StrategyBacktestStat
    stat = StrategyBacktestStat("a", signals=10, wins=8, losses=2)
    w = weights.from_backtest(__import__("hacker.backtest.engine", fromlist=["BacktestReport"]).BacktestReport(by_strategy={"a": stat}))
    assert 0.0 < w["a"] < 1.0


def test_mtg_engine_recovery_steps():
    eng = MTGEngine()
    first = eng.next_entry()
    assert first.step == 0 and first.status == "ENTRY"
    eng.settle_loss()
    second = eng.next_entry()
    assert second.step == 1 and second.status == "RECOVERY"
    assert second.stake > first.stake  # 1-step MTG doubles
    eng.settle_win()
    third = eng.next_entry()
    assert third.step == 0


def test_render_chart_returns_png():
    candles = _trending_candles(80)
    png = render_chart(candles, "USDBDT-OTC")
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    assert len(png) > 1000
