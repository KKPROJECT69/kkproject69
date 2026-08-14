"""Money Management overlay (risk-sizing gate, not directional).

This overlay never contributes direction; it evaluates whether a setup fits
configured money-management rules and attaches position-sizing guidance.
TODO: confirm stake/recovery parameters against the original methodology.
"""
from __future__ import annotations

from ..base import Strategy
from ...analysis.market_analyzer import MarketAnalysis
from ...models.candle import Candle
from ...models.enums import Direction
from ...models.signal import StrategyResult


class MoneyManagement(Strategy):
    id = "money_management"
    name = "Money Management"

    def analyze(self, analysis: MarketAnalysis, candles: list[Candle]) -> StrategyResult:
        # TODO: confirm exact rules vs original spec
        stake_pct = 1.0  # conservative default
        if analysis.volatility > analysis.last_close * 0.02:
            stake_pct = 0.5
        return StrategyResult(
            self.id,
            self.name,
            Direction.NO_TRADE,
            100.0,
            reason=f"Position-sizing overlay: suggested stake {stake_pct}% of bankroll",
            risks=[f"Suggested stake {stake_pct}% based on volatility"],
            evidence={"stake_pct": stake_pct, "volatility": analysis.volatility},
        )
