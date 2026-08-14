"""Admin authentication for the web control panel.

Password-protected with short-lived, revocable bearer tokens held in memory
and delivered as an HttpOnly, SameSite cookie. No external dependencies.
"""
from __future__ import annotations

import hmac
import secrets
import time


class AdminAuth:
    def __init__(
        self,
        username: str,
        password: str,
        cookie_name: str = "hacker_admin",
        ttl_hours: int = 24,
    ) -> None:
        self.username = username or "admin"
        self.password = password or ""
        self.cookie_name = cookie_name
        self.ttl_seconds = max(1, int(ttl_hours)) * 3600
        self._tokens: dict[str, float] = {}

    @property
    def enabled(self) -> bool:
        return bool(self.password)

    def verify(self, username: str, password: str) -> bool:
        if not self.enabled:
            return False
        return hmac.compare_digest(str(username), self.username) and hmac.compare_digest(
            str(password), self.password
        )

    def issue(self) -> str:
        self._prune()
        token = secrets.token_urlsafe(32)
        self._tokens[token] = time.time() + self.ttl_seconds
        return token

    def check(self, token: str | None) -> bool:
        if not token:
            return False
        expiry = self._tokens.get(token)
        if expiry is None:
            return False
        if expiry < time.time():
            self._tokens.pop(token, None)
            return False
        return True

    def revoke(self, token: str | None) -> None:
        if token:
            self._tokens.pop(token, None)

    def _prune(self) -> None:
        now = time.time()
        for token in [t for t, exp in self._tokens.items() if exp < now]:
            self._tokens.pop(token, None)
