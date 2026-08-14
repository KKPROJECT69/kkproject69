from datetime import UTC, datetime

from hacker.models.enums import Timeframe
from hacker.timing.engine import SignalTimingEngine


def test_target_candle_start_aligns_to_boundary():
    eng = SignalTimingEngine(lead_seconds=17.0)
    when = datetime(2026, 8, 14, 12, 0, 30, tzinfo=UTC)
    assert eng.target_candle_start(Timeframe.M1, when) == datetime(
        2026, 8, 14, 12, 1, 0, tzinfo=UTC
    )


def test_send_at_uses_lead_time():
    eng = SignalTimingEngine(lead_seconds=17.0)
    target = datetime(2026, 8, 14, 12, 1, 0, tzinfo=UTC)
    assert (target - eng.send_at(target)).total_seconds() == 17.0


def test_stale_rejection():
    eng = SignalTimingEngine(lead_seconds=17.0)
    target = datetime(2026, 8, 14, 12, 1, 0, tzinfo=UTC)
    assert eng.is_stale(target, datetime(2026, 8, 14, 12, 0, 50, tzinfo=UTC))
    assert not eng.is_stale(target, datetime(2026, 8, 14, 12, 0, 30, tzinfo=UTC))


def test_duplicate_protection():
    eng = SignalTimingEngine()
    target = datetime(2026, 8, 14, 12, 1, 0, tzinfo=UTC)
    assert not eng.already_sent("X", target)
    eng.mark_sent("X", target)
    assert eng.already_sent("X", target)
