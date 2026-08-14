"""Runtime bot controller — the single source of truth shared by the Telegram
bot and the web dashboard.

It owns the live state (bot power, signal gate), runtime settings overrides
(persisted in SQLite), the deploy lifecycle, and every admin action exposed by
the web control panel. The web layer never talks to the Telegram/storage layer
directly — it goes through this controller.
"""
from __future__ import annotations

import asyncio
import logging
import os
import platform
import time
from collections import deque
from datetime import datetime, timezone
from typing import Any

from . import __version__
from .config.settings import Settings
from .data_sources import get_market_source
from .models.enums import AccessLevel, Timeframe
from .models.signal import FinalSignal
from .storage.db import Database
from .storage.repositories import (
    AuditRepo,
    OutcomeRepoSummary,
    SettingsRepo,
    SignalRepo,
    StatsRepo,
    UserRepo,
)
from .telegram.channel import ChannelConfig
from .telegram.dispatcher import TelegramSignalDispatcher
from .telegram.sender import TelegramSignalSender

log = logging.getLogger("hacker")

# Typed runtime settings that can be edited live from the web admin panel.
# key -> coercion kind. The *default* value for each key is derived from the
# process Settings (so env vars / .env are never clobbered by an override).
SETTING_SCHEMA: dict[str, str] = {
    "min_confidence": "float",
    "min_payout": "float",
    "signal_lead_seconds": "float",
    "cooldown_seconds": "float",
    "market_source": "str",
    "require_confluence": "bool",
    "avoid_volatile": "bool",
}


def _coerce(value: Any, kind: str, default: Any) -> Any:
    if value is None:
        return default
    text = str(value).strip()
    try:
        if kind == "float":
            return float(text)
        if kind == "int":
            return int(text)
        if kind == "bool":
            return text.lower() in ("1", "true", "yes", "on")
    except (ValueError, TypeError):
        return default
    return text


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class RingLogHandler(logging.Handler):
    """Keeps the most recent log lines in memory for the web admin panel."""

    def __init__(self, capacity: int = 300) -> None:
        super().__init__()
        self.buffer: deque[str] = deque(maxlen=capacity)

    def emit(self, record: logging.LogRecord) -> None:  # noqa: D401
        try:
            self.buffer.append(self.format(record))
        except Exception:  # noqa: BLE001 - logging must never crash the app
            pass

    def tail(self, limit: int = 200) -> list[str]:
        return list(self.buffer)[-limit:]


class BotController:
    def __init__(
        self,
        settings: Settings,
        db: Database,
        pipeline,
        dispatcher: TelegramSignalDispatcher,
        channel: ChannelConfig,
        sender: TelegramSignalSender,
        registry,
        user_repo: UserRepo,
        signal_repo: SignalRepo,
        stats_repo: StatsRepo,
        settings_repo: SettingsRepo,
        audit_repo: AuditRepo,
    ) -> None:
        self.settings = settings
        self.db = db
        self.pipeline = pipeline
        self.dispatcher = dispatcher
        self.channel = channel
        self.sender = sender
        self.registry = registry
        self.user_repo = user_repo
        self.signal_repo = signal_repo
        self.stats_repo = stats_repo
        self.settings_repo = settings_repo
        self.audit_repo = audit_repo

        # Telegram runtime objects (wired from main once built)
        self.bot = None
        self.tg_app = None

        # Live state
        self.started_at: datetime | None = None
        self.running: bool = False
        self.signals_enabled: bool = True
        self.overrides: dict[str, Any] = {}
        self._source_name: str = settings.market_source
        self._tg_task: asyncio.Task | None = None

        # Telemetry
        self.log_handler = RingLogHandler()
        self.log_handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        )
        logging.getLogger("hacker").addHandler(self.log_handler)

        # Wire the dispatcher hooks to this controller (kill switch + recorder)
        self.dispatcher.enabled = self.signals_enabled_fn
        self.dispatcher.record = self.record_signal

    # ------------------------------------------------------------- helpers
    @property
    def telegram_ready(self) -> bool:
        return self.settings.telegram_ready and self.bot is not None

    def signals_enabled_fn(self) -> bool:
        return self.signals_enabled

    def _deploy_meta(self) -> dict[str, Any]:
        on_railway = bool(
            os.getenv("RAILWAY_SERVICE_NAME") or os.getenv("RAILWAY_ENVIRONMENT")
        )
        return {
            "platform": "railway" if on_railway else "local",
            "service": os.getenv("RAILWAY_SERVICE_NAME") or "local",
            "environment": os.getenv("RAILWAY_ENVIRONMENT") or "development",
            "git_commit": os.getenv("RAILWAY_GIT_COMMIT_SHA"),
            "region": os.getenv("RAILWAY_REGION"),
        }

    # ------------------------------------------------------------ lifecycle
    async def start(self) -> None:
        """Start the Telegram poller (if configured) and announce deployment."""
        self.started_at = datetime.now(timezone.utc)
        await self._load_state()
        self.running = False
        if self.telegram_ready and self.tg_app is not None:
            self._tg_task = asyncio.create_task(self._poll())
            # give the poller a moment to come up before announcing
            await asyncio.sleep(0.5)
            if self.settings.deploy_notify:
                await self.send_deploy_notification()
        else:
            log.info("Telegram not configured — web dashboard only mode")

    async def stop(self) -> None:
        """Gracefully stop the Telegram poller."""
        self.running = False
        if self._tg_task is not None:
            self._tg_task.cancel()
            try:
                await self._tg_task
            except (asyncio.CancelledError, Exception):  # noqa: BLE001
                pass
            self._tg_task = None

    async def _poll(self) -> None:
        app = self.tg_app
        try:
            await app.initialize()
            await app.start()
            await app.updater.start_polling()
            self.running = True
            log.info("Telegram bot polling started")
            while True:
                await asyncio.sleep(3600)
        except asyncio.CancelledError:
            pass
        except Exception as exc:  # noqa: BLE001
            log.error("Telegram poller crashed: %s", exc)
        finally:
            self.running = False
            try:
                await app.updater.stop()
                await app.stop()
                await app.shutdown()
            except Exception:  # noqa: BLE001
                pass

    async def start_bot(self) -> bool:
        """Start the Telegram poller if it isn't already running."""
        if not self.telegram_ready or self.tg_app is None:
            return False
        if self._tg_task is None or self._tg_task.done():
            self._tg_task = asyncio.create_task(self._poll())
        return True

    async def restart_bot(self) -> bool:
        await self.stop()
        if not self.telegram_ready or self.tg_app is None:
            return False
        self._tg_task = asyncio.create_task(self._poll())
        return True

    # -------------------------------------------------------- notifications
    async def send_deploy_notification(self) -> bool:
        """Post a 'deployed & online' notice to the Telegram channel."""
        if not self.telegram_ready or not self.channel.channel_id:
            log.info("Deploy notification skipped — Telegram not configured")
            return False
        meta = self._deploy_meta()
        text = (
            "🟢 <b>HACKER GenAI+ DEPLOYED</b>\n"
            "━━━━━━━━━━━━━━\n"
            f"🖥 Platform: <b>{meta['platform'].upper()}</b>\n"
            f"🌐 Environment: <b>{meta['environment']}</b>\n"
            f"⚙️ Service: <code>{meta['service']}</code>\n"
            f"🏷 Version: <b>v{__version__}</b>\n"
            f"🕒 Time: {_now().replace('T', ' ')[:19]} UTC\n"
            "━━━━━━━━━━━━━━\n"
            "✅ Bot is ONLINE and monitoring the markets 24/7.\n"
            "📊 Signals, access control & admin panel are live."
        )
        try:
            await self.bot.send_message(
                chat_id=self.channel.channel_id, text=text, parse_mode="HTML"
            )
            await self.audit_repo.log("system", "deploy_notification", meta["platform"])
            return True
        except Exception as exc:  # noqa: BLE001
            log.error("Deploy notification failed: %s", exc)
            return False

    async def broadcast(self, text: str) -> bool:
        if not text.strip():
            return False
        if not self.telegram_ready or not self.channel.channel_id:
            return False
        try:
            await self.bot.send_message(
                chat_id=self.channel.channel_id,
                text=text.strip(),
                parse_mode="HTML",
            )
            await self.audit_repo.log("admin", "broadcast", text[:200])
            return True
        except Exception as exc:  # noqa: BLE001
            log.error("Broadcast failed: %s", exc)
            return False

    # ------------------------------------------------------------ settings
    def _setting_defaults(self) -> dict[str, Any]:
        s = self.settings
        return {
            "min_confidence": s.min_confidence,
            "min_payout": s.min_payout,
            "signal_lead_seconds": s.signal_lead_seconds,
            "cooldown_seconds": 60.0,
            "market_source": s.market_source,
            "require_confluence": s.require_confluence,
            "avoid_volatile": s.avoid_volatile,
        }

    async def _load_state(self) -> None:
        stored = await self.settings_repo.all()
        defaults = self._setting_defaults()
        self.overrides = {
            key: _coerce(stored.get(key), SETTING_SCHEMA[key], defaults[key])
            for key in SETTING_SCHEMA
        }
        self.signals_enabled = _coerce(stored.get("signals_enabled"), "bool", True)
        self._apply_overrides()

    def _apply_overrides(self) -> None:
        pipeline = self.pipeline
        s = self.settings
        pipeline.decision_engine.min_confidence = float(
            self.overrides.get("min_confidence", s.min_confidence)
        )
        pipeline.payout_filter.min_payout = float(
            self.overrides.get("min_payout", s.min_payout)
        )
        pipeline.timing.lead_seconds = float(
            self.overrides.get("signal_lead_seconds", s.signal_lead_seconds)
        )
        pipeline.require_confluence = bool(
            self.overrides.get("require_confluence", s.require_confluence)
        )
        pipeline.avoid_volatile = bool(
            self.overrides.get("avoid_volatile", s.avoid_volatile)
        )
        pipeline.market_filters.cooldown.cooldown_seconds = float(
            self.overrides.get("cooldown_seconds", 60.0)
        )
        source_name = str(self.overrides.get("market_source", s.market_source)).lower()
        if source_name != self._source_name:
            self.pipeline.source = get_market_source(source_name)
            self._source_name = source_name

    async def set_setting(self, key: str, value: Any) -> dict[str, Any]:
        if key not in SETTING_SCHEMA:
            return {"ok": False, "error": f"unknown setting: {key}"}
        kind = SETTING_SCHEMA[key]
        default = self._setting_defaults()[key]
        coerced = _coerce(value, kind, default)
        await self.settings_repo.set(key, str(coerced))
        self.overrides[key] = coerced
        self._apply_overrides()
        await self.audit_repo.log("admin", "setting_update", f"{key}={coerced}")
        return {"ok": True, "key": key, "value": coerced}

    async def set_signals_enabled(self, enabled: bool) -> bool:
        self.signals_enabled = bool(enabled)
        await self.settings_repo.set("signals_enabled", "1" if enabled else "0")
        await self.audit_repo.log("admin", "signals_gate", "ON" if enabled else "OFF")
        log.info("Signal delivery gate set to %s", "ON" if enabled else "OFF")
        return self.signals_enabled

    async def current_settings(self) -> dict[str, Any]:
        return dict(self.overrides) | {"signals_enabled": self.signals_enabled}

    # ------------------------------------------------------------ signals
    async def record_signal(self, signal: FinalSignal, status: str = "PENDING") -> None:
        status = (status or "PENDING").upper()
        try:
            await self.signal_repo.save(
                signal.signal_id,
                session_id=signal.session_id,
                user_id=signal.user_id,
                pair=signal.pair,
                direction=signal.direction.value,
                timeframe=signal.timeframe.value,
                entry_time=signal.target_entry.isoformat(),
                target_candle=signal.target_entry.isoformat(),
                payout=signal.payout,
                confidence=signal.confidence,
                strategy=signal.strategy,
                reason=signal.reason,
                ai_verdict=signal.ai_verdict,
                risk_level=signal.risk_level,
                generated_at=(
                    signal.generated_at.isoformat() if signal.generated_at else _now()
                ),
                delivered_at=_now() if status == "DELIVERED" else None,
                status=status,
            )
        except Exception as exc:  # noqa: BLE001
            log.error("Failed to record signal: %s", exc)

    async def generate_and_dispatch(
        self, pair: str, timeframe: str
    ) -> FinalSignal | None:
        tf = Timeframe(timeframe)
        signal = await self.pipeline.generate(pair, tf)
        await self.audit_repo.log(
            "admin", "test_signal", f"{pair} {timeframe} -> "
            f"{signal.direction.value if signal else 'NO_TRADE'}"
        )
        return signal

    # -------------------------------------------------------------- queries
    async def status(self) -> dict[str, Any]:
        stats = await self.stats_repo.summary()
        return {
            "running": self.running,
            "telegram_configured": self.telegram_ready,
            "signals_enabled": self.signals_enabled,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "uptime_seconds": (
                (datetime.now(timezone.utc) - self.started_at).total_seconds()
                if self.started_at
                else 0.0
            ),
            "version": __version__,
            "python": platform.python_version(),
            "market_source": self._source_name,
            "ai_provider": self.settings.ai_provider,
            "signals_total": await self.signal_repo.count(),
            "signals_delivered": await self.signal_repo.count_delivered(),
            "users_total": await self.user_repo.count(),
            "stats": stats,
            "settings": await self.current_settings(),
            "deploy": self._deploy_meta(),
        }

    async def recent_signals(self, limit: int = 50) -> list[dict[str, Any]]:
        return await self.signal_repo.recent(limit)

    async def list_users(self) -> list[dict[str, Any]]:
        return await self.user_repo.list_all()

    async def set_user_level(self, telegram_id: int, level: str) -> dict[str, Any]:
        try:
            parsed = AccessLevel(level)
        except ValueError:
            return {"ok": False, "error": f"invalid level: {level}"}
        await self.user_repo.set_level(telegram_id, parsed)
        await self.audit_repo.log("admin", "user_level", f"{telegram_id}={parsed.value}")
        return {"ok": True, "telegram_id": telegram_id, "level": parsed.value}

    async def set_user_banned(self, telegram_id: int, banned: bool) -> dict[str, Any]:
        await self.user_repo.set_banned(telegram_id, bool(banned))
        await self.audit_repo.log(
            "admin", "user_ban", f"{telegram_id} {'BANNED' if banned else 'UNBANNED'}"
        )
        return {"ok": True, "telegram_id": telegram_id, "banned": bool(banned)}

    async def audit_log(self, limit: int = 100) -> list[dict[str, Any]]:
        return await self.audit_repo.recent(limit)

    def logs(self, limit: int = 200) -> list[str]:
        return self.log_handler.tail(limit)
