"""Authoritative 11-strategy registry.

The exact historical names/rule sets were not fully retrievable; the retained
concepts are used as scaffolds and each module is marked TODO where the
original spec should be confirmed. Swap implementations here without touching
the rest of the system.
"""
from __future__ import annotations

from .base import Strategy
from .impl.breakout import Breakout
from .impl.fakeout import Fakeout
from .impl.fvg import FairValueGap
from .impl.ifeg import IFEG
from .impl.market_structure import MarketStructure
from .impl.money_management import MoneyManagement
from .impl.mtg import MTG
from .impl.risk_control import RiskControl
from .impl.support_resistance import SupportResistance
from .impl.trendline import Trendline
from .impl.volume_imbalance import VolumeImbalance


class StrategyRegistry:
    def __init__(self, strategies: list[Strategy] | None = None) -> None:
        default: list[Strategy] = [
            SupportResistance(),
            Trendline(),
            FairValueGap(),
            Breakout(),
            Fakeout(),
            IFEG(),
            VolumeImbalance(),
            MarketStructure(),
            MTG(),
            MoneyManagement(),
            RiskControl(),
        ]
        self._strategies: dict[str, Strategy] = {s.id: s for s in (strategies or default)}

    def all(self) -> list[Strategy]:
        return list(self._strategies.values())

    def get(self, strategy_id: str) -> Strategy | None:
        return self._strategies.get(strategy_id)

    def select(self, strategy_ids: list[str] | None) -> list[Strategy]:
        if not strategy_ids:
            return self.all()
        return [s for sid in strategy_ids if (s := self._strategies.get(sid))]

    def __len__(self) -> int:
        return len(self._strategies)


DEFAULT_REGISTRY = StrategyRegistry()
