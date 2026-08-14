"""Candlestick chart rendering — fully local (matplotlib Agg, no display)."""
from __future__ import annotations

import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

from ..analysis.market_analyzer import MarketAnalysis  # noqa: E402
from ..models.candle import Candle  # noqa: E402

_GREEN = "#26a69a"
_RED = "#ef5350"


def render_chart(
    candles: list[Candle],
    pair: str,
    analysis: MarketAnalysis | None = None,
    width: float = 8.0,
    height: float = 5.0,
    dpi: int = 110,
) -> bytes:
    """Render a candlestick chart and return PNG bytes."""
    candles = candles[-80:]
    fig, ax = plt.subplots(figsize=(width, height), dpi=dpi)
    ax.set_facecolor("#0e1117")
    fig.patch.set_facecolor("#0e1117")

    body_width = 0.6
    for i, c in enumerate(candles):
        color = _GREEN if c.close >= c.open else _RED
        # wick
        ax.plot([i, i], [c.low, c.high], color=color, linewidth=0.9, solid_capstyle="round")
        # body
        top = max(c.open, c.close)
        bottom = min(c.open, c.close)
        h = max(top - bottom, 1e-9)
        ax.add_patch(Rectangle((i - body_width / 2, bottom), body_width, h, facecolor=color, edgecolor=color))

    # support / resistance lines
    if analysis is not None:
        for lvl in analysis.support_levels[:3]:
            ax.axhline(lvl, color="#3d9970", linestyle="--", linewidth=0.7, alpha=0.6)
        for lvl in analysis.resistance_levels[:3]:
            ax.axhline(lvl, color="#ff851b", linestyle="--", linewidth=0.7, alpha=0.6)

    ax.set_title(f"{pair}", color="white", fontsize=11, pad=8)
    ax.tick_params(colors="#9aa0a6", labelsize=7)
    for spine in ax.spines.values():
        spine.set_color("#2a2f35")
    ax.grid(color="#1b1f24", linewidth=0.5)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return buf.getvalue()
