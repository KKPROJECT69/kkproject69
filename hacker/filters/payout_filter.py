"""Payout filter — block signals below the configured minimum payout."""
from __future__ import annotations


class PayoutFilter:
    def __init__(self, min_payout: float = 0.0) -> None:
        self.min_payout = min_payout

    def check(self, payout: float | None) -> tuple[bool, str]:
        if payout is None:
            return True, "payout unavailable — filter skipped"
        if payout < self.min_payout:
            return False, f"payout {payout}% below minimum {self.min_payout}%"
        return True, f"payout {payout}% meets minimum"
