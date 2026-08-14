from hacker.models.enums import Direction
from hacker.models.signal import StrategyResult
from hacker.strategies.aggregator import StrategyAggregator


def _r(sid: str, direction: Direction, confidence: float) -> StrategyResult:
    return StrategyResult(sid, sid, direction, confidence)


def test_full_call_agreement():
    agg = StrategyAggregator()
    res = agg.aggregate(
        [_r("a", Direction.CALL, 80), _r("b", Direction.CALL, 75), _r("c", Direction.CALL, 70)]
    )
    assert res.direction == Direction.CALL
    assert res.agreement == 1.0
    assert res.conflicting is False


def test_conflicting_directions():
    agg = StrategyAggregator()
    res = agg.aggregate([_r("a", Direction.CALL, 70), _r("b", Direction.PUT, 70)])
    assert res.conflicting is True


def test_no_trade_outputs_ignored_as_direction():
    agg = StrategyAggregator()
    res = agg.aggregate([_r("a", Direction.CALL, 80), _r("ov", Direction.NO_TRADE, 100)])
    assert res.direction == Direction.CALL
    assert res.total_directional == 1
    assert res.total_active == 2
