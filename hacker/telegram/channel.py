"""Telegram channel routing configuration."""
from __future__ import annotations

from ..config.settings import get_settings


class ChannelConfig:
    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def channel_id(self) -> str:
        return self.settings.telegram_channel_id

    @property
    def ready(self) -> bool:
        return self.settings.telegram_ready
