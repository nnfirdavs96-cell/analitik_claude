"""Database initialization utilities."""
from sqlalchemy.ext.asyncio import AsyncEngine

from app.db.base import Base
from app.db.session import async_engine
from app.models import *  # noqa — ensures all models are registered


async def create_all_tables(engine: AsyncEngine = async_engine) -> None:
    """Create all tables. Use only in development; production uses Alembic."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_all_tables(engine: AsyncEngine = async_engine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
