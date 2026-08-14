"""HACKER GenAI+ — entrypoint.

Wires every module together and either starts the Telegram bot (when a token
+ channel are configured) or runs an offline smoke test of the pipeline.
"""
from __future__ import annotations

import asyncio
import logging

from telegram import Bot
from telegram.request import HTTPXRequest

from hacker.analysis.market_analyzer import MarketAnalyzer
from hacker.config.settings import get_settings
from hacker.data_sources import get_market_source
from hacker.decision.ai import RuleBasedAIService
from hacker.decision.engine import SignalDecisionEngine
from hacker.filters import MarketFilterEngine, NewsFilter, PayoutFilter
from hacker.models.enums import Timeframe
from hacker.pipeline import SignalPipeline
from hacker.storage.db import Database
from hacker.storage.repositories import (
    OutcomeRepo,
    SessionRepo,
    SignalRepo,
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

log = logging.getLogger("hacker")


def build_pipeline(dispatcher=None) -> SignalPipeline:
    settings = get_settings()
    return SignalPipeline(
        source=get_market_source(),
        analyzer=MarketAnalyzer(),
        registry=StrategyRegistry(),
        decision_engine=SignalDecisionEngine(
            aggregator=StrategyAggregator(),
            ai=RuleBasedAIService(),
            min_confidence=settings.min_confidence,
        ),
        payout_filter=PayoutFilter(settings.min_payout),
        news_filter=NewsFilter(),
        market_filters=MarketFilterEngine(),
        timing=SignalTimingEngine(settings.signal_lead_seconds),
        dispatcher=dispatcher,
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
    session_repo = SessionRepo(db)
    signal_repo = SignalRepo(db)
    outcome_repo = OutcomeRepo(db)
    stats_repo = StatsRepo(db)

    channel = ChannelConfig()
    sender = TelegramSignalSender()
    dispatcher = TelegramSignalDispatcher(channel=channel, sender=sender)
    pipeline = build_pipeline(dispatcher)
    registry = StrategyRegistry()

    try:
        if settings.telegram_ready:
            request = None
            if settings.telegram_proxy:
                request = HTTPXRequest(proxy=settings.telegram_proxy)
            bot = Bot(token=settings.telegram_bot_token, request=request)
            dispatcher.bot = bot
            hacker_bot = HackerBot(pipeline, user_repo, registry=registry)
            await hacker_bot.run()
        else:
            log.info("Telegram not configured — running offline smoke test")
            signal = await pipeline.generate("USDBDT_otc", Timeframe.M1)
            if signal is not None:
                print(sender.format_signal(signal))
            else:
                print("🧠 NO TRADE — no sufficiently strong setup passed all gates.")
    finally:
        await db.close()


def main() -> None:
    asyncio.run(amain())


if __name__ == "__main__":
    main()
