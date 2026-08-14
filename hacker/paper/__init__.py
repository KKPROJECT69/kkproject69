"""Paper trading engine — virtual trades, no real-money execution."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from ..models.enums import Direction, ResultType
from ..results.evaluator import ResultEvaluator


@dataclass
class PaperTrade:
    id: str
    pair: str
    direction: Direction
    stake: float
    entry_price: float
    opened_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    result: ResultType | None = None


class PaperTradingEngine:
    def __init__(
        self,
        balance: float = 10_000.0,
        stake: float = 100.0,
        payout: float = 80.0,
    ) -> None:
        self.balance = balance
        self.stake = stake
        self.payout = payout
        self.evaluator = ResultEvaluator()
        self.open_trades: dict[str, PaperTrade] = {}
        self.closed: list[PaperTrade] = []

    def open(self, pair: str, direction: Direction, entry_price: float, stake: float | None = None) -> PaperTrade:
        trade = PaperTrade(
            id=uuid4().hex[:8],
            pair=pair,
            direction=direction,
            stake=stake or self.stake,
            entry_price=entry_price,
        )
        self.balance -= trade.stake
        self.open_trades[trade.id] = trade
        return trade

    def close(self, trade_id: str, close_price: float) -> PaperTrade:
        trade = self.open_trades.pop(trade_id)
        result = self.evaluator.resolve(trade.direction, trade.entry_price, close_price)
        trade.result = result
        if result in (ResultType.DIRECT_WIN, ResultType.MTG_WIN):
            profit = trade.stake * self.payout / 100
            self.balance += trade.stake + profit
        elif result == ResultType.BREAK_EVEN:
            self.balance += trade.stake
        self.closed.append(trade)
        return trade

    @property
    def stats(self) -> dict:
        wins = sum(1 for t in self.closed if t.result in (ResultType.DIRECT_WIN, ResultType.MTG_WIN))
        losses = sum(1 for t in self.closed if t.result in (ResultType.LOSS, ResultType.MTG_LOSS))
        return {
            "balance": round(self.balance, 2),
            "open": len(self.open_trades),
            "closed": len(self.closed),
            "wins": wins,
            "losses": losses,
            "accuracy": round(wins / len(self.closed) * 100, 2) if self.closed else 0.0,
        }
