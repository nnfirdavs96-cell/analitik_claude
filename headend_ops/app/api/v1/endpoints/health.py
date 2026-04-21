"""Health and readiness endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Healthcheck")
async def health():
    return {"status": "ok", "service": "headend-ops"}


@router.get("/ready", summary="Readiness check")
async def ready(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ready", "database": "ok"}
    except Exception as e:
        return {"status": "not_ready", "database": str(e)}
