"""Typed application settings loaded from environment / .env."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Telegram
    telegram_bot_token: str = ""
    telegram_channel_id: str = ""
    telegram_proxy: str | None = None
    market_proxy: str | None = None

    # Market data
    market_source: str = "mock"  # mock | novex | oanda | cortex
    novex_base_url: str = ""
    novex_api_key: str = ""

    # News calendar
    forex_factory_url: str = ""

    # AI reasoning/approval
    ai_api_url: str = ""
    ai_api_key: str = ""

    # Signal / safety gates
    min_confidence: float = 70.0
    min_payout: float = 0.0
    signal_lead_seconds: float = 17.0

    # Storage / ops
    db_path: str = "data/hacker.db"
    log_level: str = "INFO"
    admin_ids: str = ""

    @property
    def admin_id_set(self) -> set[int]:
        return {
            int(x)
            for x in self.admin_ids.replace(" ", "").split(",")
            if x.strip().isdigit()
        }

    @property
    def telegram_ready(self) -> bool:
        return bool(self.telegram_bot_token and self.telegram_channel_id)


@lru_cache
def get_settings() -> Settings:
    return Settings()
