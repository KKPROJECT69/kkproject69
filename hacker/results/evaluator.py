"""Outcome evaluator — resolve a signal against the realized candle."""
from __future__ import annotations

from ..models.enums import Direction, ResultType


class ResultEvaluator:
    def __init__(self, epsilon: float = 1e-9) -> None:
        self.epsilon = epsilon

    def is_win(self, direction: Direction, entry_price: float, close_price: float) -> bool:
        if direction == Direction.CALL:
            return close_price > entry_price + self.epsilon
        if direction == Direction.PUT:
            return close_price < entry_price - self.epsilon
        return False

    def resolve(
        self,
        direction: Direction,
        entry_price: float,
        close_price: float,
        mtg_count: int = 0,
    ) -> ResultType:
        if direction == Direction.NO_TRADE:
            return ResultType.BREAK_EVEN
        if abs(close_price - entry_price) <= self.epsilon:
            return ResultType.BREAK_EVEN
        win = self.is_win(direction, entry_price, close_price)
        if win:
            return ResultType.MTG_WIN if mtg_count > 0 else ResultType.DIRECT_WIN
        return ResultType.MTG_LOSS if mtg_count > 0 else ResultType.LOSS
