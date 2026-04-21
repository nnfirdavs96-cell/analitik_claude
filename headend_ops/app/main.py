"""FastAPI application entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("app_startup", env=settings.APP_ENV)
    # Ensure reports directory exists
    settings.reports_path.mkdir(parents=True, exist_ok=True)
    yield
    logger.info("app_shutdown")


app = FastAPI(
    title="Headend Ops Platform",
    description="AI-powered operational reporting platform for TV headend operations",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_PREFIX)

# Serve static files (dashboard HTML, fonts)
import os
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", include_in_schema=False)
async def root():
    return {
        "service": "Headend Ops Platform",
        "version": "1.0.0",
        "docs": "/docs",
        "dashboard": "/static/dashboard.html",
    }
