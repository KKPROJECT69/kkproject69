"""Tests for the shared BotController (runtime state + access control)."""
from __future__ import annotations

import pytest
import pytest_asyncio

from hacker.analysis.market_analyzer import MarketAnalyzer
from hacker.config.settings import Settings
from hacker.data_sources.mock import MockMarketSource
from hacker.decision.engine import SignalDecisionEngine
from hacker.filters import MarketFilterEngine, NewsFilter, PayoutFilter
from hacker.pipeline import SignalPipeline
from hacker.runtime import BotController
from hacker.storage.db import Database
from hacker.storage.repositories import (
    AuditRepo,
    SettingsRepo,
    SignalRepo,
    StatsRepo,
    UserRepo,
)
from hacker.strategies.aggregator import StrategyAggregator
from hacker.strategies.registry import StrategyRegistry
from hacker.telegram import (
    ChannelConfig,
    TelegramSignalDispatcher,
    TelegramSignalSender,
)
from hacker.timing.engine import SignalTimingEngine


def _pipeline(dispatcher=None) -> SignalPipeline:
    return SignalPipeline(
        source=MockMarketSource(seed=7),
        analyzer=MarketAnalyzer(),
        registry=StrategyRegistry(),
        decision_engine=SignalDecisionEngine(StrategyAggregator(), min_confidence=70.0),
        payout_filter=PayoutFilter(0.0),
        news_filter=NewsFilter(),
        market_filters=MarketFilterEngine(),
        timing=SignalTimingEngine(17.0),
        dispatcher=dispatcher,
    )


async def _controller(tmp_path) -> tuple[BotController, Database]:
    settings = Settings(
        db_path=str(tmp_path / "test.db"),
        web_admin_password="secret",
        telegram_bot_token="",
        telegram_channel_id="",
    )
    db = Database(settings.db_path)
    await db.connect()
    channel = ChannelConfig()
    dispatcher = TelegramSignalDispatcher(channel=channel, sender=TelegramSignalSender())
    controller = BotController(
        settings=settings,
        db=db,
        pipeline=_pipeline(dispatcher),
        dispatcher=dispatcher,
        channel=channel,
        sender=TelegramSignalSender(),
        registry=StrategyRegistry(),
        user_repo=UserRepo(db),
        signal_repo=SignalRepo(db),
        stats_repo=StatsRepo(db),
        settings_repo=SettingsRepo(db),
        audit_repo=AuditRepo(db),
    )
    await controller._load_state()
    return controller, db


@pytest_asyncio.fixture
async def controller(tmp_path):
    c, db = await _controller(tmp_path)
    yield c
    await db.close()


@pytest.mark.asyncio
async def test_status_snapshot(controller):
    status = await controller.status()
    assert status["telegram_configured"] is False
    assert status["signals_enabled"] is True
    assert status["version"]
    assert "stats" in status
    assert "settings" in status


@pytest.mark.asyncio
async def test_signals_gate_toggle(controller):
    assert await controller.set_signals_enabled(False) is False
    status = await controller.status()
    assert status["signals_enabled"] is False
    assert await controller.set_signals_enabled(True) is True


@pytest.mark.asyncio
async def test_setting_override_applied(controller):
    result = await controller.set_setting("min_confidence", "80")
    assert result["ok"] is True
    assert controller.pipeline.decision_engine.min_confidence == 80.0
    assert await controller.settings_repo.get("min_confidence") == "80.0"


@pytest.mark.asyncio
async def test_unknown_setting_rejected(controller):
    result = await controller.set_setting("nonsense", "1")
    assert result["ok"] is False


@pytest.mark.asyncio
async def test_generate_records_signal(controller):
    signal = await controller.generate_and_dispatch("USDBDT_otc", "1m")
    recent = await controller.recent_signals(50)
    if signal is not None:
        assert any(r["id"] == signal.signal_id for r in recent)
        # not delivered (no Telegram in test), recorded as PENDING
        row = next(r for r in recent if r["id"] == signal.signal_id)
        assert row["status"] == "PENDING"


@pytest.mark.asyncio
async def test_gate_off_records_blocked(controller):
    await controller.set_signals_enabled(False)
    signal = await controller.generate_and_dispatch("USDBDT_otc", "1m")
    if signal is not None:
        recent = await controller.recent_signals(50)
        row = next(r for r in recent if r["id"] == signal.signal_id)
        assert row["status"] == "BLOCKED"


@pytest.mark.asyncio
async def test_user_access_control(controller):
    await controller.user_repo.upsert(123, username="trader")
    result = await controller.set_user_level(123, "VIP")
    assert result["ok"] is True
    row = await controller.user_repo.get(123)
    assert row["access_level"] == "VIP"
    await controller.set_user_banned(123, True)
    row = await controller.user_repo.get(123)
    assert row["banned"] == 1
    users = await controller.list_users()
    assert any(u["telegram_id"] == 123 for u in users)


@pytest.mark.asyncio
async def test_set_user_creates_new_user(controller):
    """Admin panel must be able to add users that never messaged the bot."""
    result = await controller.set_user(999, "VIP", True)
    assert result["ok"] is True
    row = await controller.user_repo.get(999)
    assert row is not None
    assert row["access_level"] == "VIP"
    assert row["banned"] == 1


@pytest.mark.asyncio
async def test_user_upsert_does_not_reset_level(controller):
    """A user messaging the bot (/start) must never wipe their admin-set level."""
    await controller.user_repo.upsert(321, username="trader")
    await controller.set_user_level(321, "VIP")
    await controller.user_repo.upsert(321, username="trader2")  # simulates /start
    row = await controller.user_repo.get(321)
    assert row["access_level"] == "VIP"
    assert row["username"] == "trader2"


@pytest.mark.asyncio
async def test_deploy_notify_noop_without_telegram(controller):
    assert await controller.send_deploy_notification() is False


@pytest.mark.asyncio
async def test_broadcast_noop_without_telegram(controller):
    assert await controller.broadcast("hello") is False
