"""API v1 router — aggregates all endpoint routers."""
from fastapi import APIRouter

from app.api.v1.endpoints import (
    dashboard,
    dictionaries,
    events,
    health,
    kpi,
    reports,
    review,
    telegram,
)

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(telegram.router)
api_router.include_router(events.router)
api_router.include_router(kpi.router)
api_router.include_router(reports.router)
api_router.include_router(dictionaries.router)
api_router.include_router(review.router)
api_router.include_router(dashboard.router)
