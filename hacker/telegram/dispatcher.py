"""Signal dispatcher — routes only approved signals to the configured channel."""
from __future__ import annotations

import logging

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
    ) -> None:
        self.channel = channel or ChannelConfig()
        self.sender = sender or TelegramSignalSender()
        self.bot = bot

    async def dispatch(self, signal: FinalSignal) -> None:
        text = self.sender.format_signal(signal)
        if self.bot is not None and self.channel.channel_id:
            await self.bot.send_message(
                chat_id=self.channel.channel_id, text=text, parse_mode="HTML"
            )
        else:
            log.warning(
                "Telegram not configured — signal %s (%s %s) not delivered",
                signal.signal_id,
                signal.pair,
                signal.direction.value,
            )
