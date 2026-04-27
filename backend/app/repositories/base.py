"""
Base repository providing generic CRUD operations with soft-delete support.
"""

import uuid
from typing import TypeVar, Generic, Type, Optional, List
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic async repository with soft-delete awareness."""

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    def _active_query(self):
        """Return a base query filtering out soft-deleted records."""
        query = select(self.model)
        if hasattr(self.model, "deleted_at"):
            query = query.where(self.model.deleted_at == None)
        return query

    async def get_by_id(self, entity_id: uuid.UUID) -> Optional[ModelType]:
        """Get a single entity by ID (excludes soft-deleted)."""
        query = self._active_query().where(self.model.id == entity_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        offset: int = 0,
        limit: int = 20,
    ) -> List[ModelType]:
        """Get all entities with pagination (excludes soft-deleted)."""
        query = self._active_query().offset(offset).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count(self) -> int:
        """Count all active entities."""
        query = select(func.count(self.model.id))
        if hasattr(self.model, "deleted_at"):
            query = query.where(self.model.deleted_at == None)
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def create(self, entity: ModelType) -> ModelType:
        """Persist a new entity."""
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def update(self, entity: ModelType) -> ModelType:
        """Update an existing entity."""
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def soft_delete(self, entity: ModelType) -> ModelType:
        """Soft-delete an entity by setting deleted_at."""
        entity.deleted_at = datetime.now(timezone.utc)
        await self.session.flush()
        return entity

    async def hard_delete(self, entity: ModelType) -> None:
        """Permanently delete an entity."""
        await self.session.delete(entity)
        await self.session.flush()
