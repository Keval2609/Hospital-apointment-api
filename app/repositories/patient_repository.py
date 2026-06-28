"""
Patient-specific repository.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patient import Patient
from app.repositories.base import BaseRepository


class PatientRepository(BaseRepository[Patient]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Patient, session)

    async def get_by_user_id(self, user_id: uuid.UUID) -> Patient | None:
        """Find a patient profile by the owning user's ID."""
        result = await self.session.execute(
            select(Patient).where(Patient.user_id == user_id)
        )
        return result.scalars().first()
