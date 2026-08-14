"""Session result report — consolidated on-demand partial/current report."""
from __future__ import annotations

from datetime import datetime, timezone

from ..results.statistics import SessionStatistics


class SessionReportGenerator:
    def format(
        self,
        session_id: str,
        stats: SessionStatistics,
        started_at: datetime | None = None,
        status: str = "RUNNING",
    ) -> str:
        duration = ""
        if started_at is not None:
            delta = datetime.now(timezone.utc) - started_at
            minutes = int(delta.total_seconds() // 60)
            duration = f"\n⏱ Duration: <b>{minutes} min</b>"

        lines = [
            "📊 <b>SESSION RESULT</b>",
            "━━━━━━━━━━━━━━",
            f"🆔 Session: <code>{session_id}</code>",
            f"📌 Status: <b>{status}</b>{duration}",
            f"🎯 Total signals: <b>{stats.total}</b>",
            f"🏆 Direct wins: <b>{stats.wins}</b>",
            f"🪜 MTG wins: <b>{stats.mtg_wins}</b>",
            f"❌ MTG losses: <b>{stats.mtg_losses}</b>",
            f"💥 Losses: <b>{stats.losses}</b>",
            f"🟰 Break-even: <b>{stats.breakeven}</b>",
            f"📈 Accuracy: <b>{stats.accuracy}%</b>",
            "━━━━━━━━━━━━━━",
        ]
        if stats.by_strategy:
            lines.append("🎯 <b>By strategy</b>")
            for sid, counts in stats.by_strategy.items():
                lines.append(f"• {sid}: {counts}")
        if stats.by_pair:
            lines.append("📊 <b>By pair</b>")
            for pair, counts in stats.by_pair.items():
                lines.append(f"• {pair}: {counts}")
        return "\n".join(lines)
