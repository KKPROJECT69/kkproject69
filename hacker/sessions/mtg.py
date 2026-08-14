"""1-Step MTG (recovery) support — fully local money-management discipline.

When a signal loses, the MTG path doubles the stake on the next same-direction
signal until a win occurs (configurable multiplier & cap). This module only
*computes* the recovery state/stake — it never places broker trades.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MTGState:
    base_stake: float = 100.0
    multiplier: float = 2.0
    max_steps: int = 1  # 1-step MTG
    losses: int = 0
    total_staked: float = 0.0
    recovered: int = 0

    @property
    def current_stake(self) -> float:
        return self.base_stake * (self.multiplier ** min(self.losses, self.max_steps))

    def on_win(self) -> None:
        self.recovered += 1
        self.losses = 0

    def on_loss(self) -> None:
        self.losses += 1
        self.total_staked += self.current_stake


@dataclass
class MTGResult:
    stake: float
    step: int
    status: str  # ENTRY | RECOVERY | COMPLETE


class MTGEngine:
    def __init__(self, state: MTGState | None = None) -> None:
        self.state = state or MTGState()

    def next_entry(self) -> MTGResult:
        if self.state.losses == 0:
            return MTGResult(self.state.current_stake, 0, "ENTRY")
        return MTGResult(self.state.current_stake, self.state.losses, "RECOVERY")

    def settle_win(self) -> None:
        self.state.on_win()

    def settle_loss(self) -> None:
        self.state.on_loss()

    def reset(self) -> None:
        self.state.losses = 0
        self.state.total_staked = 0.0
        self.state.recovered = 0
