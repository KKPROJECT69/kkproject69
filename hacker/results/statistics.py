"""Session / strategy statistics."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from ..models.enums import ResultType


@dataclass
class SessionStatistics:
    total: int = 0
    wins: int = 0
    mtg_wins: int = 0
    mtg_losses: int = 0
    losses: int = 0
    breakeven: int = 0
    by_strategy: dict[str, dict] = field(default_factory=lambda: defaultdict(dict))
    by_pair: dict[str, dict] = field(default_factory=lambda: defaultdict(dict))

    def record(self, result: ResultType, strategy: str = "", pair: str = "") -> None:
        self.total += 1
        if result == ResultType.DIRECT_WIN:
            self.wins += 1
        elif result == ResultType.MTG_WIN:
            self.mtg_wins += 1
        elif result == ResultType.MTG_LOSS:
            self.mtg_losses += 1
        elif result == ResultType.LOSS:
            self.losses += 1
        elif result == ResultType.BREAK_EVEN:
            self.breakeven += 1
        if strategy:
            self.by_strategy[strategy][result.value] = self.by_strategy[strategy].get(result.value, 0) + 1
        if pair:
            self.by_pair[pair][result.value] = self.by_pair[pair].get(result.value, 0) + 1

    @property
    def accuracy(self) -> float:
        wins = self.wins + self.mtg_wins
        return round(wins / self.total * 100, 2) if self.total else 0.0

    def summary(self) -> dict:
        return {
            "total": self.total,
            "wins": self.wins,
            "mtg_wins": self.mtg_wins,
            "mtg_losses": self.mtg_losses,
            "losses": self.losses,
            "breakeven": self.breakeven,
            "accuracy": self.accuracy,
            "by_strategy": dict(self.by_strategy),
            "by_pair": dict(self.by_pair),
        }
