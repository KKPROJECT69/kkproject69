"""Telegram bot — button-first UX, all menus wired to real actions."""
from __future__ import annotations

import asyncio
import io
import logging
from datetime import datetime, timezone

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

from ..analysis.market_analyzer import MarketAnalyzer
from ..backtest.engine import BacktestEngine
from ..charting.render import render_chart
from ..config.settings import get_settings
from ..models.enums import AccessLevel, Direction, ResultType, Timeframe
from ..models.signal import FinalSignal
from ..pipeline import SignalPipeline
from ..results.evaluator import ResultEvaluator
from ..results.loss_review import LossReviewer
from ..scanning.scanner import DEFAULT_OTC_PAIRS, PairScanner
from ..storage.repositories import StatsRepo, UserRepo
from ..users.access import AccessManager
from .sender import TelegramSignalSender
from .state import StateStore
from .ui import (
    admin_menu,
    back_menu,
    filters_menu,
    live_session_menu,
    main_menu,
    pair_menu,
    paper_menu,
    payout_filter_menu,
    session_running_menu,
    strategy_menu,
    timeframe_menu,
)

log = logging.getLogger(__name__)

ABOUT = (
    "🚀 <b>HACKER GenAI+</b> — AI Trading Assistant\n"
    "━━━━━━━━━━━━━━\n"
    "📈 Market analysis · 11 strategies · AI decisions · timed signals\n"
    "🧪 Backtesting · paper trading · payout ranking · MTG recovery\n"
    "⚠️ Signals are analysis only — not financial advice."
)


class HackerBot:
    def __init__(
        self,
        pipeline: SignalPipeline,
        user_repo: UserRepo,
        stats_repo: StatsRepo | None = None,
        registry=None,
        access: AccessManager | None = None,
        controller=None,
    ) -> None:
        self.settings = get_settings()
        self.pipeline = pipeline
        self.user_repo = user_repo
        self.stats_repo = stats_repo
        self.registry = registry
        self.access = access or AccessManager(user_repo, self.settings.admin_id_set)
        self.controller = controller
        self.sender = TelegramSignalSender()
        self.analyzer = MarketAnalyzer()
        self.evaluator = ResultEvaluator()
        self.loss_reviewer = LossReviewer()
        self.scanner = PairScanner(pipeline.source)
        self.states = StateStore()

    # ------------------------------------------------------------------ app
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
        app.add_handler(CommandHandler("admin", self.cmd_admin))
        app.add_handler(CallbackQueryHandler(self.on_callback))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.on_text))
        app.add_error_handler(self.on_error)
        return app

    async def run(self) -> None:
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
                log.warning("Telegram connect attempt %d/%d failed: %s", attempt, max_attempts, exc)
                try:
                    await app.stop()
                    await app.shutdown()
                except Exception:  # noqa: BLE001
                    pass
                if attempt >= max_attempts:
                    raise
                await asyncio.sleep(min(2 ** (attempt - 1), 60))

    async def on_error(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        log.error("Telegram error: %s", context.error)

    # ------------------------------------------------------------- commands
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        if user is not None:
            await self.user_repo.upsert(user.id, username=user.username)
            if await self.access.is_banned(user.id):
                await update.effective_message.reply_text(
                    "⛔ <b>ACCESS DENIED</b>\nYour account has been banned.",
                    parse_mode="HTML",
                )
                return
        await update.effective_message.reply_text(
            f"Welcome to <b>HACKER GenAI+</b> 👋\n\n{ABOUT}",
            parse_mode="HTML",
            reply_markup=main_menu(),
        )

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.effective_message.reply_text(ABOUT, parse_mode="HTML", reply_markup=main_menu())

    async def cmd_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        if user is None:
            return
        level = await self.access.level(user.id)
        if level != AccessLevel.ADMIN:
            await update.effective_message.reply_text(
                "🔒 <b>ADMIN ONLY</b>\nThis menu is restricted to administrators.",
                parse_mode="HTML",
            )
            return
        await update.effective_message.reply_text(
            "🛠 <b>ADMIN CONTROL</b>\nManage the bot, signals & users 👇",
            parse_mode="HTML",
            reply_markup=admin_menu(),
        )

    async def on_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        if user is None:
            return
        state = self.states.get(user.id)
        if state.pending_action == "broadcast":
            state.pending_action = None
            if self.controller is not None:
                ok = await self.controller.broadcast(update.effective_message.text or "")
                await update.effective_message.reply_text(
                    "📢 Broadcast sent." if ok else "❌ Broadcast failed (Telegram not configured).",
                    reply_markup=admin_menu(),
                )
            return
        await update.effective_message.reply_text("Use the buttons below 👇", reply_markup=main_menu())

    # ------------------------------------------------------------ callbacks
    async def on_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()
        data = query.data or ""
        user = update.effective_user
        if user is None:
            return
        state = self.states.get(user.id)

        if await self.access.is_banned(user.id):
            await query.answer("Your account has been banned.", show_alert=True)
            return

        # ---- admin controls (ADMIN only) --------------------------------
        if data.startswith("admin:"):
            if await self.access.level(user.id) != AccessLevel.ADMIN:
                await query.answer("Admin only", show_alert=True)
                return
            await self._handle_admin(query, data, state)
            return

        # ---- pair / timeframe selectors (context-sensitive) ------------
        if data.startswith("pair:"):
            state.pair = data.split(":", 1)[1]
            await query.edit_message_text(
                f"Pair: <b>{state.pair}</b>\nChoose timeframe 👇",
                parse_mode="HTML",
                reply_markup=timeframe_menu("tf"),
            )
            return
        if data.startswith("tf:"):
            state.timeframe = Timeframe(data.split(":", 1)[1])
            await self._finish_action(query, state)
            return
        if data.startswith("strategy:"):
            state.strategy_id = data.split(":", 1)[1]
            await query.edit_message_text(
                f"Strategy selected. Choose pair 👇", reply_markup=pair_menu("pair")
            )
            return
        if data.startswith("payout:"):
            state.min_payout = float(data.split(":", 1)[1])
            await query.edit_message_text(
                f"💰 Min payout set to <b>{state.min_payout:.0f}%</b>",
                parse_mode="HTML",
                reply_markup=payout_filter_menu(state.min_payout),
            )
            return
        if data == "filter:toggle_news":
            state.skip_news = not state.skip_news
            await query.edit_message_text(
                "Market filters 👇", reply_markup=filters_menu(state.skip_news)
            )
            return

        # ---- menus -------------------------------------------------------
        if data == "menu:main":
            await query.edit_message_text("Main menu 👇", reply_markup=main_menu())
        elif data == "menu:live_signal":
            state.pending_action = "live_signal"
            await query.edit_message_text("Choose pair 👇", reply_markup=pair_menu("pair"))
        elif data == "menu:otc_signal":
            if not await self.access.can(user.id, "otc_future_signal"):
                await query.edit_message_text(
                    "🔒 <b>PREMIUM ONLY</b>\nOTC Future Signal requires PREMIUM/VIP access.",
                    parse_mode="HTML",
                    reply_markup=back_menu(),
                )
                return
            state.pending_action = "otc_signal"
            await query.edit_message_text("Choose OTC pair 👇", reply_markup=pair_menu("pair"))
        elif data == "menu:market_analysis":
            state.pending_action = "market_analysis"
            await query.edit_message_text("Choose pair 👇", reply_markup=pair_menu("pair"))
        elif data == "menu:ai_analysis":
            state.pending_action = "ai_analysis"
            await query.edit_message_text("Choose pair 👇", reply_markup=pair_menu("pair"))
        elif data == "menu:news_signal":
            text = await self._run_news_signal()
            await query.edit_message_text(text, parse_mode="HTML", reply_markup=back_menu())
        elif data == "menu:backtest":
            text = await self._run_backtest(state.pair, state.timeframe)
            await query.edit_message_text(text, parse_mode="HTML", reply_markup=back_menu())
        elif data == "menu:payout_ranking":
            text = await self._run_payout_ranking()
            await query.edit_message_text(text, parse_mode="HTML", reply_markup=back_menu())
        elif data == "menu:payout_filter":
            await query.edit_message_text(
                "Set minimum payout 👇", reply_markup=payout_filter_menu(state.min_payout)
            )
        elif data == "menu:market_filters":
            await query.edit_message_text("Market filters 👇", reply_markup=filters_menu(state.skip_news))
        elif data == "menu:live_session":
            await query.edit_message_text("Choose session type 👇", reply_markup=live_session_menu())
        elif data == "session:combined":
            await self._start_session(query, state, "COMBINED", None)
        elif data == "session:single":
            await query.edit_message_text("Choose a strategy 👇", reply_markup=strategy_menu(self.registry))
        elif data == "session:stop":
            await self._stop_session(query, state)
        elif data == "session:result":
            await self._show_session_result(query, state)
        elif data == "menu:session_result":
            await self._show_session_result(query, state)
        elif data == "menu:paper":
            await query.edit_message_text("Paper trading 👇", reply_markup=paper_menu())
        elif data.startswith("paper:open:"):
            direction = Direction(data.split(":")[2])
            candles = await self.pipeline.source.get_candles(state.pair, Timeframe.M1, 1)
            price = candles[-1].close if candles else 0.0
            trade = state.paper.open(state.pair, direction, price)
            await query.edit_message_text(
                f"🧪 Paper trade opened:\n{state.pair} {direction.value} @ {price}\nID <code>{trade.id}</code>",
                parse_mode="HTML",
                reply_markup=paper_menu(),
            )
        elif data == "paper:close":
            text = await self._paper_close(state)
            await query.edit_message_text(text, parse_mode="HTML", reply_markup=paper_menu())
        elif data == "paper:status":
            s = state.paper.stats
            await query.edit_message_text(
                f"🧪 <b>PAPER ACCOUNT</b>\nBalance: <b>{s['balance']}</b>\n"
                f"Open: {s['open']} | Closed: {s['closed']}\n"
                f"Wins: {s['wins']} | Losses: {s['losses']} | Acc: {s['accuracy']}%",
                parse_mode="HTML",
                reply_markup=paper_menu(),
            )
        elif data == "menu:account":
            level = await self.access.level(user.id)
            await query.edit_message_text(
                f"👤 <b>MY ACCOUNT</b>\nUser ID: <code>{user.id}</code>\n"
                f"Access: <b>{level.value}</b>\nPair: {state.pair}\nTimeframe: {state.timeframe.value}",
                parse_mode="HTML",
                reply_markup=back_menu(),
            )
        elif data in ("menu:vip", "menu:premium"):
            level = await self.access.level(user.id)
            allowed = level.value in ("VIP", "ADMIN") if data == "menu:vip" else level.value in ("PREMIUM", "VIP", "ADMIN")
            text = (
                ("👑 <b>VIP ZONE</b>\nPremium signals, loss-recovery & exclusive features." if allowed
                 else f"🔒 This area requires higher access. Your level: <b>{level.value}</b>")
            )
            await query.edit_message_text(text, parse_mode="HTML", reply_markup=back_menu())
        elif data == "menu:help":
            await query.edit_message_text(ABOUT, parse_mode="HTML", reply_markup=back_menu())
        else:
            await query.edit_message_text("🚧 Feature coming soon.", reply_markup=back_menu())

    # ------------------------------------------------------------- admin
    async def _handle_admin(self, query, data: str, state) -> None:
        controller = self.controller
        if controller is None:
            await query.edit_message_text("⚠️ Admin panel unavailable.", reply_markup=back_menu())
            return

        if data == "admin:status":
            status = await controller.status()
            text = (
                "🛠 <b>SYSTEM STATUS</b>\n"
                "━━━━━━━━━━━━━━\n"
                f"🟢 Bot: <b>{'ONLINE' if status['running'] else 'STANDBY'}</b>\n"
                f"🚦 Signals: <b>{'ON' if status['signals_enabled'] else 'OFF'}</b>\n"
                f"📡 Signals: <b>{status['signals_total']}</b> "
                f"({status['signals_delivered']} delivered)\n"
                f"👥 Users: <b>{status['users_total']}</b>\n"
                f"📈 Win rate: <b>{status['stats']['accuracy']}%</b>\n"
                f"⏱ Uptime: <b>{int(status['uptime_seconds'])}s</b>"
            )
            await query.edit_message_text(text, parse_mode="HTML", reply_markup=admin_menu())
        elif data == "admin:toggle_signals":
            enabled = await controller.set_signals_enabled(not controller.signals_enabled)
            await query.edit_message_text(
                f"🚦 Signal delivery: <b>{'ON ✅' if enabled else 'OFF 🚫'}</b>",
                parse_mode="HTML",
                reply_markup=admin_menu(),
            )
        elif data == "admin:ping":
            ok = await controller.send_deploy_notification()
            await query.edit_message_text(
                "🔔 Deploy ping sent." if ok else "❌ Telegram not configured.",
                parse_mode="HTML",
                reply_markup=admin_menu(),
            )
        elif data == "admin:broadcast":
            state.pending_action = "broadcast"
            await query.edit_message_text(
                "📢 Send the broadcast text now 👇", reply_markup=admin_menu()
            )
        elif data == "admin:users":
            users = await controller.list_users()
            lines = ["👥 <b>USERS</b>", "━━━━━━━━━━━━━━"]
            for u in users[:10]:
                banned = " 🚫BANNED" if u.get("banned") else ""
                lines.append(
                    f"• <code>{u['telegram_id']}</code> {u.get('username') or ''} "
                    f"— <b>{u.get('access_level')}</b>{banned}"
                )
            lines.append(f"Total: <b>{len(users)}</b>")
            await query.edit_message_text(
                "\n".join(lines), parse_mode="HTML", reply_markup=admin_menu()
            )
        else:
            await query.edit_message_text("🛠 Admin menu 👇", reply_markup=admin_menu())

    # ------------------------------------------------------------ actions
    async def _finish_action(self, query, state) -> None:
        action = state.pending_action
        state.pending_action = None
        if action == "live_signal":
            signal, candles = await self._signal_with_candles(state)
            if signal is None:
                await query.edit_message_text(
                    "🧠 <b>AI VERDICT: NO TRADE</b>\nNo sufficiently strong setup passed all gates.",
                    parse_mode="HTML",
                    reply_markup=back_menu(),
                )
                return
            await self._send_signal_with_chart(query, signal, candles)
        elif action == "otc_signal":
            signal, candles = await self._signal_with_candles(state)
            if signal is None:
                await query.edit_message_text("🧠 <b>NO TRADE</b> (OTC)", parse_mode="HTML", reply_markup=back_menu())
                return
            await self._send_signal_with_chart(query, signal, candles)
        elif action == "market_analysis":
            candles = await self.pipeline.source.get_candles(state.pair, state.timeframe, 200)
            analysis = self.analyzer.analyze(candles, state.pair)
            text = (
                "📈 <b>MARKET ANALYSIS</b>\n━━━━━━━━━━━━━━\n"
                f"Pair: <b>{state.pair}</b> ({state.timeframe.value})\n"
                f"Trend: <b>{analysis.trend}</b>\nStructure: <b>{analysis.structure}</b>\n"
                f"Momentum: {analysis.momentum}%\nRSI: {analysis.rsi}\n"
                f"Volatility (ATR): {analysis.volatility}\nLast close: {analysis.last_close}"
            )
            png = render_chart(candles, state.pair, analysis)
            await query.message.reply_photo(
                photo=io.BytesIO(png), caption=text, parse_mode="HTML", reply_markup=back_menu()
            )
        elif action == "ai_analysis":
            candles = await self.pipeline.source.get_candles(state.pair, state.timeframe, 200)
            analysis = self.analyzer.analyze(candles, state.pair)
            results = [s.analyze(analysis, candles) for s in self.registry.all()]
            lines = [f"🧠 <b>AI ANALYSIS — {state.pair}</b>", "━━━━━━━━━━━━━━"]
            for r in results:
                if r.is_directional:
                    lines.append(f"🎯 {r.name}: <b>{r.direction.value}</b> ({r.confidence:.0f}%)")
                    if r.reason:
                        lines.append(f"   ↳ {r.reason}")
                else:
                    lines.append(f"🛡 {r.name}: {r.reason}")
            await query.edit_message_text("\n".join(lines), parse_mode="HTML", reply_markup=back_menu())

    async def _signal_with_candles(self, state) -> tuple[FinalSignal | None, list]:
        candles = await self.pipeline.source.get_candles(state.pair, state.timeframe, 200)
        signal = await self.pipeline.generate(
            state.pair,
            state.timeframe,
            strategy_ids=[state.strategy_id] if state.strategy_id else None,
            user_id=state.user_id,
            min_payout=state.min_payout,
            skip_news=state.skip_news,
        )
        return signal, candles

    async def _send_signal_with_chart(self, query, signal: FinalSignal, candles: list) -> None:
        analysis = self.analyzer.analyze(candles, signal.pair)
        text = self.sender.format_signal(signal)
        png = render_chart(candles, signal.pair, analysis)
        await query.message.reply_photo(
            photo=io.BytesIO(png),
            caption=text,
            parse_mode="HTML",
            reply_markup=back_menu(),
        )

    async def _run_news_signal(self) -> str:
        events = await self._fetch_news()
        if not events:
            return "📰 <b>NEWS SIGNAL</b>\nNo calendar configured (FOREX_FACTORY_URL empty)."
        lines = ["📰 <b>UPCOMING HIGH-IMPACT EVENTS</b>", "━━━━━━━━━━━━━━"]
        for e in events[:8]:
            lines.append(f"• {e.title} ({e.currency}) — {e.date.strftime('%d/%m %H:%M')}")
        return "\n".join(lines)

    async def _fetch_news(self):
        from ..calendar.forex_factory import ForexFactoryCalendar
        try:
            return await ForexFactoryCalendar().fetch_week()
        except Exception:  # noqa: BLE001
            return []

    async def _run_backtest(self, pair: str, timeframe: Timeframe) -> str:
        candles = await self.pipeline.source.get_candles(pair, timeframe, 400)
        engine = BacktestEngine(registry=self.registry, analyzer=self.analyzer,
                                decision_engine=self.pipeline.decision_engine)
        report = engine.run(candles, pair)
        lines = [
            f"🧪 <b>BACKTEST — {pair} {timeframe.value}</b>",
            "━━━━━━━━━━━━━━",
            f"🎯 Signals: <b>{report.signals}</b>",
            f"🏆 Wins: <b>{report.wins}</b> | ❌ Losses: <b>{report.losses}</b>",
            f"📈 Accuracy: <b>{report.accuracy}%</b>",
        ]
        if report.by_strategy:
            lines.append("🎯 <b>By strategy</b>")
            for sid, stat in sorted(report.by_strategy.items(), key=lambda kv: -kv[1].accuracy):
                lines.append(f"• {sid}: {stat.wins}W/{stat.losses}L ({stat.accuracy}%)")
        return "\n".join(lines)

    async def _run_payout_ranking(self) -> str:
        ranking = await self.scanner.payout_ranking()
        lines = ["💰 <b>PAYOUT RANKING (OTC)</b>", "━━━━━━━━━━━━━━"]
        for i, p in enumerate(ranking[:10], 1):
            payout = f"{p.payout}%" if p.payout is not None else "n/a"
            lines.append(f"{i}. <b>{p.pair}</b> — {payout}")
        return "\n".join(lines)

    # ------------------------------------------------------------- session
    async def _start_session(self, query, state, session_type: str, strategy_id: str | None) -> None:
        if state.session_active:
            await query.edit_message_text("⏹ A session is already running.", reply_markup=session_running_menu())
            return
        from uuid import uuid4

        from ..results.statistics import SessionStatistics

        state.session_id = uuid4().hex[:12]
        state.session_type = session_type
        state.session_active = True
        state.session_stats = SessionStatistics()
        state.session_task = asyncio.create_task(
            self._session_loop(state, session_type, strategy_id)
        )
        await query.edit_message_text(
            f"🚀 <b>{session_type} SESSION STARTED</b>\n"
            f"Pair: <b>{state.pair}</b> ({state.timeframe.value})\n"
            f"Strategy: <b>{strategy_id or 'ALL 11'}</b>\n"
            "Monitoring… signals will be sent at candle timing.",
            parse_mode="HTML",
            reply_markup=session_running_menu(),
        )

    async def _stop_session(self, query, state) -> None:
        if state.session_task is not None:
            state.session_task.cancel()
            state.session_task = None
        state.session_active = False
        await query.edit_message_text(
            "⏹ Session stopped.", parse_mode="HTML", reply_markup=back_menu()
        )

    async def _show_session_result(self, query, state) -> None:
        from ..reporting.session_report import SessionReportGenerator
        gen = SessionReportGenerator()
        stats = state.session_stats
        text = gen.format(state.session_id or "n/a", stats, status=("RUNNING" if state.session_active else "STOPPED"))
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=(session_running_menu() if state.session_active else back_menu()))

    async def _session_loop(self, state, session_type: str, strategy_id: str | None) -> None:
        pair = state.pair
        timeframe = state.timeframe
        pending = None
        try:
            while state.session_active:
                # resolve previous signal's outcome first
                if pending is not None:
                    await self._resolve_pending(state, pending)
                    pending = None
                signal = await self.pipeline.generate(
                    pair, timeframe,
                    strategy_ids=[strategy_id] if strategy_id else None,
                    session_id=state.session_id,
                    user_id=state.user_id,
                    min_payout=state.min_payout,
                    skip_news=state.skip_news,
                )
                if signal is not None:
                    candles = await self.pipeline.source.get_candles(pair, timeframe, 200)
                    pending = (signal, candles[-1].close if candles else 0.0)
                    state.session_stats.total += 1
                await asyncio.sleep(3.0)
        except asyncio.CancelledError:
            pass

    async def _resolve_pending(self, state, pending) -> None:
        signal, entry = pending
        candles = await self.pipeline.source.get_candles(signal.pair, signal.timeframe, 200)
        if not candles:
            return
        close = candles[-1].close
        result = self.evaluator.resolve(signal.direction, entry, close)
        state.session_stats.record(result, strategy=signal.strategy, pair=signal.pair)
        if self.stats_repo is not None:
            for sid in (signal.strategy.split(", ") if signal.strategy else []):
                await self.stats_repo.record(sid, signal.pair, result)

    # ------------------------------------------------------------- paper
    async def _paper_close(self, state) -> str:
        if not state.paper.open_trades:
            return "🧪 No open paper trades."
        candles = await self.pipeline.source.get_candles(state.pair, Timeframe.M1, 1)
        close = candles[-1].close if candles else 0.0
        lines = []
        for trade_id in list(state.paper.open_trades.keys()):
            trade = state.paper.close(trade_id, close)
            lines.append(f"Closed {trade.pair} {trade.direction.value}: <b>{trade.result.value}</b>")
        lines.append(f"Balance: <b>{state.paper.balance:.0f}</b>")
        return "🧪 " + "\n".join(lines)
