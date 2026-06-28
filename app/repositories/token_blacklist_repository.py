"""
Token blacklist repository for tracking revoked refresh tokens.
"""

from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.token_blacklist import TokenBlacklist
from app.repositories.base import BaseRepository


class TokenBlacklistRepository(BaseRepository[TokenBlacklist]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(TokenBlacklist, session)

    async def is_blacklisted(self, jti: str) -> bool:
        """Check whether a token JTI has been revoked."""
        result = await self.session.execute(
            select(TokenBlacklist).where(TokenBlacklist.jti == jti)
        )
        return result.scalars().first() is not None

    async def cleanup_expired(self) -> int:
        """Delete blacklist entries whose tokens have already expired.

        Returns the number of rows removed.
        """
        now = datetime.now(timezone.utc)
        result = await self.session.execute(
            delete(TokenBlacklist).where(TokenBlacklist.expires_at < now)
        )
        await self.session.flush()
        return result.rowcount  # type: ignore[return-value]
