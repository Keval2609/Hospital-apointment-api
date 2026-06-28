"""
Generic base repository providing common CRUD operations.

All entity-specific repositories inherit from ``BaseRepository`` and may
add their own query methods.
"""

import uuid
from typing import Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Generic async CRUD repository.

    Parameters
    ----------
    model : type[ModelType]
        The SQLAlchemy model class this repository manages.
    session : AsyncSession
        The active database session (injected via DI).
    """

    def __init__(self, model: type[ModelType], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    async def get_by_id(self, entity_id: uuid.UUID) -> ModelType | None:
        """Return a single entity by its primary key, or ``None``."""
        result = await self.session.execute(
            select(self.model).where(self.model.id == entity_id)
        )
        return result.scalars().first()

    async def get_all(
        self, *, offset: int = 0, limit: int = 20
    ) -> list[ModelType]:
        """Return a paginated list of entities."""
        result = await self.session.execute(
            select(self.model).offset(offset).limit(limit)
        )
        return list(result.scalars().all())

    async def count(self) -> int:
        """Return the total number of rows for this model."""
        result = await self.session.execute(
            select(func.count()).select_from(self.model)
        )
        return result.scalar_one()

    async def create(self, entity: ModelType) -> ModelType:
        """Persist a new entity and return it with generated fields populated."""
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def update(self, entity: ModelType, update_data: dict) -> ModelType:
        """Apply partial updates from a dict and return the refreshed entity."""
        for key, value in update_data.items():
            if value is not None:
                setattr(entity, key, value)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def delete(self, entity: ModelType) -> None:
        """Remove an entity from the database."""
        await self.session.delete(entity)
        await self.session.flush()
