"""
Doctor-specific repository with specialty and availability queries.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.doctor import Doctor
from app.repositories.base import BaseRepository


class DoctorRepository(BaseRepository[Doctor]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Doctor, session)

    async def get_by_user_id(self, user_id: uuid.UUID) -> Doctor | None:
        """Find a doctor profile by the owning user's ID."""
        result = await self.session.execute(
            select(Doctor).where(Doctor.user_id == user_id)
        )
        return result.scalars().first()

    async def get_by_specialty(
        self, specialty: str, *, offset: int = 0, limit: int = 20
    ) -> list[Doctor]:
        """Return doctors filtered by specialty (case-insensitive)."""
        result = await self.session.execute(
            select(Doctor)
            .where(Doctor.specialty.ilike(f"%{specialty}%"))
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_available(
        self, *, offset: int = 0, limit: int = 20
    ) -> list[Doctor]:
        """Return only doctors marked as available."""
        result = await self.session.execute(
            select(Doctor)
            .where(Doctor.is_available.is_(True))
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_license_number(self, license_number: str) -> Doctor | None:
        """Find a doctor by their unique license number."""
        result = await self.session.execute(
            select(Doctor).where(Doctor.license_number == license_number)
        )
        return result.scalars().first()
