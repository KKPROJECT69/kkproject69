"""Telegram bot — application, handlers, polling (button-first UX)."""
from __future__ import annotations

import asyncio
import logging

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telegram.request import HTTPXRequest

from ..config.settings import get_settings
from ..models.enums import Timeframe
from ..pipeline import SignalPipeline
from ..storage.repositories import UserRepo
from .sender import TelegramSignalSender
from .ui import back_menu, live_session_menu, main_menu, strategy_menu

log = logging.getLogger(__name__)

ABOUT = (
    "🚀 <b>HACKER GenAI+</b> — AI Trading Assistant\n"
    "Market analysis · 11 strategies · AI decisions · timed signals.\n"
    "Signals are analysis only — not financial advice."
)


class HackerBot:
    def __init__(
        self,
        pipeline: SignalPipeline,
        user_repo: UserRepo,
        registry=None,
    ) -> None:
        self.settings = get_settings()
        self.pipeline = pipeline
        self.user_repo = user_repo
        self.registry = registry
        self.sender = TelegramSignalSender()

    def build(self) -> Application:
        request = None
        if self.settings.telegram_proxy:
            request = HTTPXRequest(proxy=self.settings.telegram_proxy)
        builder = Application.builder().token(self.settings.telegram_bot_token)
        if request is not None:
            builder = builder.request(request)
        app = builder.build()

        app.add_handler(CommandHandler("start", self.cmd_start))
        app.add_handler(CommandHandler("help", self.cmd_help))
        app.add_handler(CallbackQueryHandler(self.on_callback))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.on_text))
        app.add_error_handler(self.on_error)
        return app

    async def on_error(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        log.error("Telegram error: %s", context.error)

    async def run(self) -> None:
        """Start polling with resilient connect: retry with exponential
        backoff so a temporary Telegram outage (e.g. network/provider issues)
        does not kill the bot. Only after all attempts fail does it re-raise.
        """
        max_attempts = 8
        for attempt in range(1, max_attempts + 1):
            app = self.build()
            try:
                await app.initialize()
                await app.start()
                await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
                log.info("Telegram bot polling started")
                await app.updater.idle()
                return
            except Exception as exc:  # noqa: BLE001
                log.warning(
                    "Telegram connect attempt %d/%d failed: %s",
                    attempt,
                    max_attempts,
                    exc,
                )
                try:
                    await app.stop()
                    await app.shutdown()
                except Exception:  # noqa: BLE001
                    pass
                if attempt >= max_attempts:
                    raise
                await asyncio.sleep(min(2 ** (attempt - 1), 60))

    # ---- handlers -------------------------------------------------------
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        if user is not None:
            await self.user_repo.upsert(user.id, username=user.username)
        await update.effective_message.reply_text(
            f"Welcome to <b>HACKER GenAI+</b> 👋\n\n{ABOUT}",
            parse_mode="HTML",
            reply_markup=main_menu(),
        )

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.effective_message.reply_text(ABOUT, parse_mode="HTML", reply_markup=main_menu())

    async def on_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.effective_message.reply_text(
            "Use the buttons below 👇", reply_markup=main_menu()
        )

    async def on_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()
        data = query.data or ""

        if data == "menu:main":
            await query.edit_message_text("Main menu 👇", reply_markup=main_menu())
        elif data == "menu:live_session":
            await query.edit_message_text("Choose session type 👇", reply_markup=live_session_menu())
        elif data == "session:single":
            await query.edit_message_text("Choose a strategy 👇", reply_markup=strategy_menu(self.registry))
        elif data == "menu:live_signal":
            text = await self._run_live_signal()
            await query.edit_message_text(text, parse_mode="HTML", reply_markup=back_menu())
        elif data == "menu:market_analysis":
            text = await self._run_market_analysis()
            await query.edit_message_text(text, parse_mode="HTML", reply_markup=back_menu())
        elif data == "menu:help":
            await query.edit_message_text(ABOUT, parse_mode="HTML", reply_markup=back_menu())
        else:
            await query.edit_message_text(
                "🚧 This feature is scaffolded and will be wired in the next build phase.",
                reply_markup=back_menu(),
            )

    # ---- actions --------------------------------------------------------
    async def _run_live_signal(self) -> str:
        signal = await self.pipeline.generate("USDBDT_otc", Timeframe.M1)
        if signal is None:
            return "🧠 <b>AI VERDICT: NO TRADE</b>\nNo sufficiently strong setup passed all gates."
        return self.sender.format_signal(signal)

    async def _run_market_analysis(self) -> str:
        candles = await self.pipeline.source.get_candles("USDBDT_otc", Timeframe.M5, count=200)
        analysis = self.pipeline.analyzer.analyze(candles, "USDBDT_otc")
        return (
            "📈 <b>MARKET ANALYSIS</b>\n"
            "━━━━━━━━━━━━━━\n"
            f"Pair: <b>USDBDT_otc</b>\n"
            f"Trend: <b>{analysis.trend}</b>\n"
            f"Structure: <b>{analysis.structure}</b>\n"
            f"Momentum: {analysis.momentum}%\n"
            f"RSI: {analysis.rsi}\n"
            f"Volatility (ATR): {analysis.volatility}\n"
            f"Last close: {analysis.last_close}"
        )
