"""User access management — FREE / PREMIUM / VIP / ADMIN, server-side gates."""
from __future__ import annotations

from ..models.enums import AccessLevel
from ..storage.repositories import UserRepo

FEATURE_GATES: dict[str, set[AccessLevel]] = {
    "live_session": {AccessLevel.FREE, AccessLevel.PREMIUM, AccessLevel.VIP, AccessLevel.ADMIN},
    "manual_signal": {AccessLevel.FREE, AccessLevel.PREMIUM, AccessLevel.VIP, AccessLevel.ADMIN},
    "otc_future_signal": {AccessLevel.PREMIUM, AccessLevel.VIP, AccessLevel.ADMIN},
    "vip_zone": {AccessLevel.VIP, AccessLevel.ADMIN},
    "premium": {AccessLevel.PREMIUM, AccessLevel.VIP, AccessLevel.ADMIN},
    "admin": {AccessLevel.ADMIN},
}


class AccessManager:
    def __init__(self, user_repo: UserRepo, admin_ids: set[int] | None = None) -> None:
        self.user_repo = user_repo
        self.admin_ids = admin_ids or set()

    async def level(self, user_id: int) -> AccessLevel:
        if user_id in self.admin_ids:
            return AccessLevel.ADMIN
        row = await self.user_repo.get(user_id)
        if row is None:
            return AccessLevel.FREE
        try:
            return AccessLevel(row["access_level"])
        except ValueError:
            return AccessLevel.FREE

    async def can(self, user_id: int, feature: str) -> bool:
        level = await self.level(user_id)
        return level in FEATURE_GATES.get(feature, {AccessLevel.ADMIN})
