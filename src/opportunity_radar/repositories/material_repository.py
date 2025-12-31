"""Material repository for data access."""

from typing import List, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseRepository
from ..models.material import Material


class MaterialRepository(BaseRepository[Material]):
    """Repository for Material CRUD operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(Material, db)

    async def get_by_user_id(
        self,
        user_id: str,
        material_type: Optional[str] = None,
        batch_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Material]:
        """Get materials for a user with optional filters."""
        conditions = [Material.user_id == user_id]

        if material_type:
            conditions.append(Material.material_type == material_type)

        if batch_id:
            conditions.append(Material.batch_id == batch_id)

        query = (
            select(Material)
            .where(and_(*conditions))
            .order_by(Material.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_latest_by_type(
        self,
        user_id: str,
        material_type: str,
        batch_id: Optional[str] = None,
    ) -> Optional[Material]:
        """Get the latest version of a material type for a user."""
        conditions = [
            Material.user_id == user_id,
            Material.material_type == material_type,
        ]

        if batch_id:
            conditions.append(Material.batch_id == batch_id)

        query = (
            select(Material)
            .where(and_(*conditions))
            .order_by(Material.version.desc())
            .limit(1)
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_next_version(
        self,
        user_id: str,
        material_type: str,
        batch_id: Optional[str] = None,
    ) -> int:
        """Get the next version number for a material type."""
        latest = await self.get_latest_by_type(user_id, material_type, batch_id)
        return (latest.version + 1) if latest else 1

    async def create_material(
        self,
        user_id: str,
        material_type: str,
        content: str,
        batch_id: Optional[str] = None,
        metadata_json: Optional[dict] = None,
    ) -> Material:
        """Create a new material with auto-versioning."""
        version = await self.get_next_version(user_id, material_type, batch_id)

        material = Material(
            user_id=user_id,
            material_type=material_type,
            content=content,
            batch_id=batch_id,
            version=version,
            metadata_json=metadata_json,
        )

        self.db.add(material)
        await self.db.commit()
        await self.db.refresh(material)

        return material
