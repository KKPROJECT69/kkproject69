"""Weekly report generator."""
from __future__ import annotations

from ..storage.repositories import StatsRepo


class WeeklyReportGenerator:
    def __init__(self, stats_repo: StatsRepo) -> None:
        self.stats_repo = stats_repo

    async def generate(self) -> str:
        rows = await self.stats_repo.get_all()
        if not rows:
            return "📊 <b>WEEKLY REPORT</b>\nNo recorded performance yet."
        lines = ["📊 <b>WEEKLY REPORT</b>", "━━━━━━━━━━━━━━"]
        for row in rows:
            total = sum(
                row.get(k, 0) for k in ("wins", "mtg_wins", "losses", "breakeven")
            )
            wins = row.get("wins", 0) + row.get("mtg_wins", 0)
            acc = f"{wins / total * 100:.0f}%" if total else "n/a"
            lines.append(
                f"🎯 {row['strategy_id']} · {row['pair']}\n"
                f"   {wins}W / {row.get('losses', 0)}L · acc {acc}"
            )
        return "\n".join(lines)
