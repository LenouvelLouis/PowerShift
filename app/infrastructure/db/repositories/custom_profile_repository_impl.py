"""Repository for custom hourly load profiles (CRUD on custom_load_profiles table)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.infrastructure.db.models.custom_profile_model import CustomLoadProfileModel


class CustomProfileRepositoryImpl:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_demand_id(self, demand_id: uuid.UUID) -> CustomLoadProfileModel | None:
        """Return the custom profile for a demand, or None if not set."""
        result = await self._session.execute(
            select(CustomLoadProfileModel).where(CustomLoadProfileModel.demand_id == demand_id)
        )
        return result.scalar_one_or_none()

    async def upsert(self, demand_id: uuid.UUID, profile_data: list[float]) -> CustomLoadProfileModel:
        """Create or replace the custom profile for a demand."""
        existing = await self.get_by_demand_id(demand_id)
        if existing is not None:
            existing.profile_data = profile_data
            existing.created_at = datetime.now(UTC)
            await self._session.flush()
            return existing

        row = CustomLoadProfileModel(
            demand_id=demand_id,
            profile_data=profile_data,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def delete_by_demand_id(self, demand_id: uuid.UUID) -> bool:
        """Delete the custom profile for a demand. Returns True if a row was removed."""
        existing = await self.get_by_demand_id(demand_id)
        if existing is None:
            return False
        await self._session.delete(existing)
        await self._session.flush()
        return True

    async def get_all_as_dict(self) -> dict[str, list[float]]:
        """Return all custom profiles keyed by demand_id string.

        Used by the simulation pipeline to bulk-load custom profiles.
        """
        result = await self._session.execute(select(CustomLoadProfileModel))
        rows = result.scalars().all()
        return {str(row.demand_id): row.profile_data for row in rows}
