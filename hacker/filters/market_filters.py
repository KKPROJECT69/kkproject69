"""Market filters — pair allowlist, cooldown, and duplicate-adjacent guards."""
from __future__ import annotations

from datetime import UTC, datetime


class PairFilter:
    def __init__(self, allowed_pairs: list[str] | None = None) -> None:
        self.allowed = allowed_pairs or []

    def check(self, pair: str) -> tuple[bool, str]:
        if self.allowed and pair not in self.allowed:
            return False, f"{pair} is not in the allowed pairs"
        return True, "ok"


class CooldownFilter:
    def __init__(self, cooldown_seconds: float = 60.0) -> None:
        self.cooldown_seconds = cooldown_seconds
        self._last: dict[str, datetime] = {}

    def check(self, pair: str, when: datetime | None = None) -> tuple[bool, str]:
        when = when or datetime.now(UTC)
        last = self._last.get(pair)
        if last is not None and (when - last).total_seconds() < self.cooldown_seconds:
            return False, "cooldown active for this pair"
        self._last[pair] = when
        return True, "ok"


class MarketFilterEngine:
    def __init__(
        self,
        cooldown: CooldownFilter | None = None,
        pair_filter: PairFilter | None = None,
    ) -> None:
        self.cooldown = cooldown or CooldownFilter()
        self.pair_filter = pair_filter or PairFilter()

    def apply(self, pair: str, when: datetime | None = None) -> tuple[bool, list[str]]:
        reasons: list[str] = []
        passed = True
        ok, reason = self.pair_filter.check(pair)
        if not ok:
            passed = False
            reasons.append(reason)
        ok, reason = self.cooldown.check(pair, when)
        if not ok:
            passed = False
            reasons.append(reason)
        return passed, reasons
