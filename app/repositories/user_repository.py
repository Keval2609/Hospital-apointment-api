"""
User-specific repository with email look-up and role filtering.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import UserRole
from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> User | None:
        """Find a user by their unique email address."""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalars().first()

    async def get_by_role(
        self, role: UserRole, *, offset: int = 0, limit: int = 20
    ) -> list[User]:
        """Return users filtered by role with pagination."""
        result = await self.session.execute(
            select(User).where(User.role == role).offset(offset).limit(limit)
        )
        return list(result.scalars().all())
