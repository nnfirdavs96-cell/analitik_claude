"""FastAPI dependency injectors."""
from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.base import AIProvider
from app.ai.provider_factory import get_primary_provider
from app.db.session import get_async_session


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_async_session():
        yield session


def get_ai_provider() -> AIProvider:
    return get_primary_provider()
