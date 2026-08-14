from hacker.analysis.market_analyzer import MarketAnalysis
from hacker.decision.engine import SignalDecisionEngine
from hacker.models.enums import Direction
from hacker.models.signal import StrategyResult


def _analysis() -> MarketAnalysis:
    return MarketAnalysis(
        pair="X",
        trend="UP",
        structure="BULLISH",
        momentum=1.0,
        rsi=55.0,
        volatility=0.1,
        support_levels=[],
        resistance_levels=[],
        fvg=[],
        breakout_level=1.0,
        breakdown_level=1.0,
        last_close=100.0,
    )


def _r(direction: Direction, confidence: float, sid: str = "s") -> StrategyResult:
    return StrategyResult(sid, sid, direction, confidence)


def test_below_gate_no_trade():
    eng = SignalDecisionEngine(min_confidence=70.0)
    decision = eng.decide([_r(Direction.CALL, 60.0)], _analysis())
    assert decision.direction == Direction.NO_TRADE
    assert decision.approved is False


def test_conflict_no_trade():
    eng = SignalDecisionEngine(min_confidence=70.0)
    decision = eng.decide(
        [_r(Direction.CALL, 80.0, "a"), _r(Direction.PUT, 80.0, "b")], _analysis()
    )
    assert decision.direction == Direction.NO_TRADE
    assert decision.approved is False


def test_agreement_approved():
    eng = SignalDecisionEngine(min_confidence=70.0)
    decision = eng.decide(
        [_r(Direction.CALL, 80.0, "a"), _r(Direction.CALL, 76.0, "b")], _analysis()
    )
    assert decision.direction == Direction.CALL
    assert decision.approved is True
