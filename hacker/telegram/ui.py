"""Button-first Telegram UI (inline keyboard menus)."""
from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from ..strategies.registry import StrategyRegistry

BACK = ("⬅️ Back", "menu:main")


def _grid(items: list[tuple[str, str]], cols: int = 2) -> list[list[InlineKeyboardButton]]:
    rows: list[list[InlineKeyboardButton]] = []
    for i in range(0, len(items), cols):
        rows.append(
            [InlineKeyboardButton(text, callback_data=cb) for text, cb in items[i : i + cols]]
        )
    return rows


def main_menu() -> InlineKeyboardMarkup:
    items = [
        ("🚀 LIVE SESSION", "menu:live_session"),
        ("📡 LIVE SIGNAL", "menu:live_signal"),
        ("🔮 OTC FUTURE SIGNAL", "menu:otc_signal"),
        ("📈 MARKET ANALYSIS", "menu:market_analysis"),
        ("📰 NEWS SIGNAL", "menu:news_signal"),
        ("🧠 AI ANALYSIS", "menu:ai_analysis"),
        ("🛡️ MARKET FILTERS", "menu:market_filters"),
        ("💰 PAYOUT FILTER", "menu:payout_filter"),
        ("📊 SESSION RESULT", "menu:session_result"),
        ("🧪 PAPER TRADING", "menu:paper_trading"),
        ("📚 AI TRADING COURSE", "menu:course"),
        ("👑 VIP ZONE", "menu:vip"),
        ("💎 PREMIUM", "menu:premium"),
        ("⚙️ SETTINGS", "menu:settings"),
        ("👤 MY ACCOUNT", "menu:account"),
        ("ℹ️ HELP / ABOUT", "menu:help"),
    ]
    return InlineKeyboardMarkup(_grid(items))


def live_session_menu() -> InlineKeyboardMarkup:
    items = [
        ("🧩 COMBINED SESSION", "session:combined"),
        ("🎯 SINGLE STRATEGY", "session:single"),
        BACK,
    ]
    return InlineKeyboardMarkup(_grid(items))


def strategy_menu(registry: StrategyRegistry | None = None) -> InlineKeyboardMarkup:
    registry = registry or StrategyRegistry()
    items = [(f"🎯 {s.name}", f"strategy:{s.id}") for s in registry.all()]
    items.append(BACK)
    return InlineKeyboardMarkup(_grid(items))


def back_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(_grid([BACK]))
