from datetime import UTC, datetime, timedelta

from hacker.filters.market_filters import CooldownFilter, PairFilter
from hacker.filters.payout_filter import PayoutFilter


def test_payout_filter():
    f = PayoutFilter(min_payout=80)
    assert f.check(75.0)[0] is False
    assert f.check(85.0)[0] is True
    assert f.check(None)[0] is True  # no payout data -> skip filter


def test_pair_filter():
    f = PairFilter(["USD"])
    assert f.check("USD")[0] is True
    assert f.check("EUR")[0] is False


def test_cooldown_filter():
    f = CooldownFilter(cooldown_seconds=60)
    now = datetime(2026, 8, 14, 12, 0, 0, tzinfo=UTC)
    assert f.check("X", now)[0] is True
    assert f.check("X", now + timedelta(seconds=10))[0] is False
    assert f.check("X", now + timedelta(seconds=61))[0] is True
