"""Application configuration loaded from environment variables."""
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    APP_ENV: str = "development"
    APP_DEBUG: bool = False
    APP_SECRET_KEY: str = "change-me"
    APP_LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://headend:headend_pass@localhost:5432/headend_ops"
    DATABASE_URL_SYNC: str = "postgresql+psycopg2://headend:headend_pass@localhost:5432/headend_ops"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_MAX_TOKENS: int = 2000
    OPENAI_TEMPERATURE: float = 0.1
    AI_CONFIDENCE_THRESHOLD: float = 0.65

    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_MODE: str = "polling"
    TELEGRAM_WEBHOOK_URL: str = ""
    TELEGRAM_WEBHOOK_SECRET: str = ""
    TELEGRAM_ALLOWED_CHAT_IDS: str = ""

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"

    # Reports
    REPORTS_DIR: str = "/app/reports_output"

    # KPI weights
    KPI_WEIGHT_INCIDENT: float = 0.40
    KPI_WEIGHT_RESOLUTION: float = 0.20
    KPI_WEIGHT_WORK: float = 0.20
    KPI_WEIGHT_REPEAT: float = 0.10
    KPI_WEIGHT_AI_QUALITY: float = 0.10

    @property
    def allowed_chat_ids(self) -> List[int]:
        if not self.TELEGRAM_ALLOWED_CHAT_IDS:
            return []
        return [int(x.strip()) for x in self.TELEGRAM_ALLOWED_CHAT_IDS.split(",") if x.strip()]

    @property
    def reports_path(self) -> Path:
        p = Path(self.REPORTS_DIR)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
