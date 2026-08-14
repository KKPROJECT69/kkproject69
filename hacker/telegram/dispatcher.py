"""Signal dispatcher — routes only approved signals to the configured channel.

The dispatcher supports two runtime hooks so the web control panel has full
authority over the bot:

- ``enabled`` — callable returning whether signal delivery is allowed. When it
  returns ``False`` the signal is recorded but **not** pushed to Telegram
  (the admin "kill switch").
- ``record`` — async callable(signal, delivered) used to persist the signal.
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Awaitable

from ..models.signal import FinalSignal
from .channel import ChannelConfig
from .sender import TelegramSignalSender

log = logging.getLogger(__name__)


class TelegramSignalDispatcher:
    def __init__(
        self,
        channel: ChannelConfig | None = None,
        sender: TelegramSignalSender | None = None,
        bot=None,
        enabled: Callable[[], bool] | None = None,
        record: Callable[[FinalSignal, str], Awaitable[None]] | None = None,
    ) -> None:
        self.channel = channel or ChannelConfig()
        self.sender = sender or TelegramSignalSender()
        self.bot = bot
        self.enabled = enabled or (lambda: True)
        self.record = record

    async def dispatch(self, signal: FinalSignal) -> None:
        text = self.sender.format_signal(signal)

        # Gate off => record and drop without delivering (admin kill switch).
        if not self.enabled():
            if self.record is not None:
                await self.record(signal, "BLOCKED")
            log.warning("Signal gate disabled — %s not delivered", signal.signal_id)
            return

        if self.bot is not None and self.channel.channel_id:
            try:
                await self.bot.send_message(
                    chat_id=self.channel.channel_id, text=text, parse_mode="HTML"
                )
                status = "DELIVERED"
            except Exception as exc:  # noqa: BLE001
                log.error("Failed to deliver signal %s: %s", signal.signal_id, exc)
                status = "FAILED"
        else:
            log.warning(
                "Telegram not configured — signal %s (%s %s) not delivered",
                signal.signal_id,
                signal.pair,
                signal.direction.value,
            )
            status = "PENDING"

        if self.record is not None:
            await self.record(signal, status)
