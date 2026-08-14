"""HACKER GenAI+ — production entrypoint.

Runs three things in one asyncio process:

1. The Telegram bot (long-polling) — when a token + channel are configured.
2. The FastAPI web dashboard + admin control panel (always on, bound to
   ``0.0.0.0:$PORT`` for Railway).
3. The shared :class:`BotController` that both of the above talk to, so the
   admin panel has full control over the bot (power, signal gate, users,
   settings) in real time.

On startup it announces "deployed & online" to the Telegram channel.
"""
from __future__ import annotations

import asyncio
import logging

import uvicorn
from telegram import Bot
from telegram.request import HTTPXRequest

from hacker.analysis.confluence import ConfluenceChecker
from hacker.analysis.market_analyzer import MarketAnalyzer
from hacker.analysis.regime import RegimeDetector
from hacker.config.settings import get_settings
from hacker.data_sources import get_market_source
from hacker.decision.ai import build_ai_service
from hacker.decision.engine import SignalDecisionEngine
from hacker.filters import MarketFilterEngine, NewsFilter, PayoutFilter
from hacker.models.enums import Timeframe
from hacker.pipeline import SignalPipeline
from hacker.runtime import BotController
from hacker.storage.db import Database
from hacker.storage.repositories import (
    AuditRepo,
    OutcomeRepo,
    SettingsRepo,
    SignalRepo,
    SessionRepo,
    StatsRepo,
    UserRepo,
)
from hacker.strategies.aggregator import StrategyAggregator
from hacker.strategies.registry import StrategyRegistry
from hacker.telegram import (
    ChannelConfig,
    HackerBot,
    TelegramSignalDispatcher,
    TelegramSignalSender,
)
from hacker.timing.engine import SignalTimingEngine
from hacker.web import create_app

log = logging.getLogger("hacker")


def build_pipeline(dispatcher=None, source=None) -> SignalPipeline:
    settings = get_settings()
    market_source = source or get_market_source()
    return SignalPipeline(
        source=market_source,
        analyzer=MarketAnalyzer(),
        registry=StrategyRegistry(),
        decision_engine=SignalDecisionEngine(
            aggregator=StrategyAggregator(),
            ai=build_ai_service(),
            min_confidence=settings.min_confidence,
        ),
        payout_filter=PayoutFilter(settings.min_payout),
        news_filter=NewsFilter(),
        market_filters=MarketFilterEngine(),
        timing=SignalTimingEngine(settings.signal_lead_seconds),
        dispatcher=dispatcher,
        confluence=ConfluenceChecker(market_source),
        regime_detector=RegimeDetector(),
        require_confluence=settings.require_confluence,
        avoid_volatile=settings.avoid_volatile,
    )


async def amain() -> None:
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    db = Database(settings.db_path)
    await db.connect()
    user_repo = UserRepo(db)
    session_repo = SessionRepo(db)  # noqa: F841  (kept for parity/future wiring)
    signal_repo = SignalRepo(db)
    outcome_repo = OutcomeRepo(db)  # noqa: F841
    stats_repo = StatsRepo(db)
    settings_repo = SettingsRepo(db)
    audit_repo = AuditRepo(db)

    channel = ChannelConfig()
    sender = TelegramSignalSender()
    dispatcher = TelegramSignalDispatcher(channel=channel, sender=sender)
    pipeline = build_pipeline(dispatcher)
    registry = StrategyRegistry()

    controller = BotController(
        settings=settings,
        db=db,
        pipeline=pipeline,
        dispatcher=dispatcher,
        channel=channel,
        sender=sender,
        registry=registry,
        user_repo=user_repo,
        signal_repo=signal_repo,
        stats_repo=stats_repo,
        settings_repo=settings_repo,
        audit_repo=audit_repo,
    )

    # --- Telegram wiring -------------------------------------------------
    if settings.telegram_ready:
        request = (
            HTTPXRequest(proxy=settings.telegram_proxy)
            if settings.telegram_proxy
            else None
        )
        bot = Bot(token=settings.telegram_bot_token, request=request)
        dispatcher.bot = bot
        controller.bot = bot
        hacker_bot = HackerBot(
            pipeline,
            user_repo,
            stats_repo=stats_repo,
            registry=registry,
            controller=controller,
        )
        controller.tg_app = hacker_bot.build()
    else:
        log.info("Telegram not configured — running web dashboard only")

    # --- Start bot poller + announce deployment --------------------------
    await controller.start()

    # --- Web server (main blocking task) ---------------------------------
    app = create_app(controller)
    config = uvicorn.Config(
        app,
        host=settings.web_host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        access_log=False,
        proxy_headers=True,
        forwarded_allow_ips="*",
    )
    server = uvicorn.Server(config)
    log.info("Web dashboard listening on http://%s:%s", settings.web_host, settings.port)
    try:
        await server.serve()
    finally:
        log.info("Shutting down…")
        await controller.stop()
        await db.close()


def main() -> None:
    asyncio.run(amain())


if __name__ == "__main__":
    main()
