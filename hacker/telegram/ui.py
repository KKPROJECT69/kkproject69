"""Button-first Telegram UI (inline keyboard menus)."""
from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from ..models.enums import Timeframe
from ..strategies.registry import StrategyRegistry

BACK = ("⬅️ Back", "menu:main")

PAIRS = [
    "USDBDT-OTC", "USDPKR-OTC", "BTCUSD-OTC", "EURUSD-OTC", "GBPUSD-OTC",
    "USDJPY-OTC", "AUDUSD-OTC", "USDCAD-OTC", "EURGBP-OTC", "USDCHF-OTC",
]

TIMEFRAMES = [Timeframe.M1, Timeframe.M5, Timeframe.M15, Timeframe.M30, Timeframe.H1]


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
        ("🧪 BACKTEST", "menu:backtest"),
        ("💰 PAYOUT RANKING", "menu:payout_ranking"),
        ("🛡️ MARKET FILTERS", "menu:market_filters"),
        ("💰 PAYOUT FILTER", "menu:payout_filter"),
        ("📊 SESSION RESULT", "menu:session_result"),
        ("🧪 PAPER TRADING", "menu:paper"),
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


def pair_menu(prefix: str = "pair") -> InlineKeyboardMarkup:
    items = [(p, f"{prefix}:{p}") for p in PAIRS]
    items.append(BACK)
    return InlineKeyboardMarkup(_grid(items))


def timeframe_menu(prefix: str = "tf") -> InlineKeyboardMarkup:
    items = [(f"⏱ {tf.value}", f"{prefix}:{tf.value}") for tf in TIMEFRAMES]
    items.append(BACK)
    return InlineKeyboardMarkup(_grid(items))


def payout_filter_menu(current: float = 0.0) -> InlineKeyboardMarkup:
    options = [0.0, 70.0, 75.0, 80.0, 85.0, 90.0]
    items = []
    for opt in options:
        label = f"{'✅ ' if opt == current else ''}💵 {opt:.0f}%" if opt else "🚫 OFF"
        items.append((label, f"payout:{opt:.0f}"))
    items.append(BACK)
    return InlineKeyboardMarkup(_grid(items))


def paper_menu() -> InlineKeyboardMarkup:
    items = [
        ("📈 OPEN CALL", "paper:open:CALL"),
        ("📉 OPEN PUT", "paper:open:PUT"),
        ("🔒 CLOSE (resolve)", "paper:close"),
        ("📊 STATUS", "paper:status"),
        BACK,
    ]
    return InlineKeyboardMarkup(_grid(items))


def filters_menu(skip_news: bool = False) -> InlineKeyboardMarkup:
    items = [
        (f"📰 News filter: {'ON ✅' if not skip_news else 'OFF 🚫'}", "filter:toggle_news"),
        ("↩️ Back", "menu:main"),
    ]
    return InlineKeyboardMarkup(_grid(items))


def session_running_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("⏹ STOP SESSION", callback_data="session:stop")],
         [InlineKeyboardButton("📊 CURRENT RESULT", callback_data="session:result")]]
    )


def back_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(_grid([BACK]))


def admin_menu() -> InlineKeyboardMarkup:
    items = [
        ("📊 SYSTEM STATUS", "admin:status"),
        ("🚦 TOGGLE SIGNALS", "admin:toggle_signals"),
        ("👥 USERS", "admin:users"),
        ("📢 BROADCAST", "admin:broadcast"),
        ("🔔 DEPLOY PING", "admin:ping"),
        ("⬅️ Back", "menu:main"),
    ]
    return InlineKeyboardMarkup(_grid(items))
