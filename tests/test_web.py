"""Tests for the FastAPI web dashboard + admin control panel."""
from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

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
from hacker.web import create_app


async def _app(tmp_path):
    settings = Settings(
        db_path=str(tmp_path / "web.db"),
        web_admin_username="admin",
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
        pipeline=SignalPipeline(
            source=MockMarketSource(seed=7),
            analyzer=MarketAnalyzer(),
            registry=StrategyRegistry(),
            decision_engine=SignalDecisionEngine(StrategyAggregator(), min_confidence=70.0),
            payout_filter=PayoutFilter(0.0),
            news_filter=NewsFilter(),
            market_filters=MarketFilterEngine(),
            timing=SignalTimingEngine(17.0),
        ),
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
    return create_app(controller), db


@pytest_asyncio.fixture
async def app(tmp_path):
    application, db = await _app(tmp_path)
    yield application
    await db.close()


@pytest.mark.asyncio
async def test_healthz(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/healthz")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_home_page(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/")
        assert r.status_code == 200
        assert "HACKER" in r.text


@pytest.mark.asyncio
async def test_admin_requires_login(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/admin")
        assert r.status_code == 303
        assert "/login" in r.headers["location"]


@pytest.mark.asyncio
async def test_login_flow_and_admin_access(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.post("/login", data={"username": "admin", "password": "nope"})
        assert r.status_code == 200
        assert "Invalid credentials" in r.text

        r = await c.post("/login", data={"username": "admin", "password": "secret"})
        assert r.status_code == 303
        assert r.headers["location"] == "/admin"

        r = await c.get("/admin")
        assert r.status_code == 200
        assert "Control Panel" in r.text


@pytest.mark.asyncio
async def test_admin_api_requires_auth(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/api/admin/logs")
        assert r.status_code == 401


@pytest.mark.asyncio
async def test_admin_api_actions_after_login(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        await c.post("/login", data={"username": "admin", "password": "secret"})
        r = await c.post("/api/admin/signals", data={"enabled": "off"})
        assert r.status_code == 303
        status = await c.get("/api/status")
        assert status.json()["signals_enabled"] is False

        await c.post(
            "/api/admin/users",
            data={"telegram_id": "555", "level": "VIP", "banned": "0"},
        )
        r = await c.get("/api/admin/logs")
        assert r.status_code == 200
        assert isinstance(r.json()["logs"], list)


@pytest.mark.asyncio
async def test_admin_add_user_creates_row(tmp_path):
    """Regression: adding a brand-new user from the panel must insert a row."""
    application, db = await _app(tmp_path)
    try:
        async with AsyncClient(
            transport=ASGITransport(app=application), base_url="http://test"
        ) as c:
            await c.post("/login", data={"username": "admin", "password": "secret"})
            r = await c.post(
                "/api/admin/users",
                data={"telegram_id": "777", "level": "PREMIUM", "banned": "1"},
            )
            assert r.status_code == 303
        row = await db.fetchone("SELECT * FROM users WHERE telegram_id = 777")
        assert row is not None
        assert row["access_level"] == "PREMIUM"
        assert row["banned"] == 1
    finally:
        await db.close()
