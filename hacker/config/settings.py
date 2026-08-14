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
    market_source: str = "auto"  # auto (router) | mock
    quotex_base_url: str = "https://quotex-proxy-pal.lovable.app/api/public"
    quotex_ws_url: str = "wss://quotex-proxy-pal.lovable.app/api/public/ws"
    novex_payout_url: str = "https://novexai.org/api.php"
    oanda_base_url: str = "https://api-fxpractice.oanda.com"
    oanda_api_key: str = ""
    oanda_account_id: str = ""

    # News calendar
    forex_factory_url: str = ""

    # AI reasoning/approval — 100% free options (local default = zero error)
    ai_provider: str = "local"  # local | gemini | groq
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    # Signal / safety gates
    min_confidence: float = 70.0
    min_payout: float = 0.0
    signal_lead_seconds: float = 17.0
    require_confluence: bool = False
    avoid_volatile: bool = False

    # Storage / ops
    db_path: str = "data/hacker.db"
    log_level: str = "INFO"
    admin_ids: str = ""

    # Web dashboard / admin control panel
    port: int = 8000  # Railway injects PORT
    web_host: str = "0.0.0.0"
    web_admin_username: str = "admin"
    web_admin_password: str = ""  # empty => admin panel disabled
    web_cookie_name: str = "hacker_admin"
    web_session_ttl_hours: int = 24

    # Deployment notification (sent to the Telegram channel on startup)
    deploy_notify: bool = True

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
