"""Branded signal / result / loss-review message formatting."""
from __future__ import annotations

from ..models.enums import ResultType
from ..models.signal import FinalSignal

RISK_WARNING = "⚠️ Trading involves risk. This is analysis, not financial advice."


class TelegramSignalSender:
    def format_signal(self, signal: FinalSignal) -> str:
        entry = signal.target_entry.strftime("%H:%M:%S UTC")
        payout = f"{signal.payout}%" if signal.payout is not None else "N/A"
        return (
            "🚀 <b>HACKER GenAI+ SIGNAL</b>\n"
            "━━━━━━━━━━━━━━\n"
            f"📊 Pair: <b>{signal.pair}</b>\n"
            f"🎯 Action: <b>{signal.direction.value}</b>\n"
            f"⏱ Timeframe: <b>{signal.timeframe.value}</b>\n"
            f"🕒 Entry: <b>{entry}</b> (NEXT CANDLE)\n"
            f"💰 Payout: <b>{payout}</b>\n"
            f"🎯 Confidence: <b>{signal.confidence:.0f}%</b>\n"
            f"🛡 Risk: <b>{signal.risk_level}</b>\n"
            f"🧠 Strategy: {signal.strategy}\n"
            f"📝 Why: {signal.reason}\n"
            f"✅ AI Verdict: <b>{signal.ai_verdict}</b>\n"
            f"🆔 ID: <code>{signal.signal_id}</code>\n"
            "━━━━━━━━━━━━━━\n"
            f"<i>{RISK_WARNING}</i>"
        )

    def format_result(
        self,
        pair: str,
        result: ResultType,
        mtg_count: int = 0,
        signal_id: str | None = None,
    ) -> str:
        if result == ResultType.DIRECT_WIN:
            title = "🏆 DIRECT WIN"
        elif result == ResultType.MTG_WIN:
            title = f"🏆 MTG WIN (recovered in {mtg_count})"
        elif result == ResultType.BREAK_EVEN:
            title = "🟰 BREAK-EVEN"
        else:
            title = "❌ LOSS"
        return (
            f"{title}\n"
            "━━━━━━━━━━━━━━\n"
            f"📊 Pair: <b>{pair}</b>\n"
            + (f"🆔 ID: <code>{signal_id}</code>\n" if signal_id else "")
            + f"<i>{RISK_WARNING}</i>"
        )

    def format_loss_review(self, pair: str, review: dict, signal_id: str | None = None) -> str:
        reason = review.get("failure_reason", "unknown")
        strategy_impact = review.get("strategy_impact", "n/a")
        learning = review.get("learning", "n/a")
        status = review.get("strategy_status", "n/a")
        return (
            "🧠 <b>AI LOSS REVIEW</b>\n"
            "━━━━━━━━━━━━━━\n"
            f"📊 Pair: <b>{pair}</b>\n"
            f"🔍 Failure reason: {reason}\n"
            f"🧩 Strategy impact: {strategy_impact}\n"
            f"📈 Strategy status: {status}\n"
            f"💡 Learning: {learning}\n"
            + (f"🆔 ID: <code>{signal_id}</code>\n" if signal_id else "")
        )
