"""Application configuration loaded from environment variables."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Database
    database_url: str = "sqlite:///./data/app.db"

    # Redis / Celery
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
    celery_task_always_eager: bool = True

    # Auth
    jwt_secret: str = "change-me-in-production-please"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Storage
    upload_folder: str = "./data/uploads"
    results_folder: str = "./data/results"
    models_folder: str = "./models"
    max_upload_size_gb: int = 10

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # Tier limits (GB)
    free_tier_storage_gb: float = 5
    pro_tier_storage_gb: float = 100
    enterprise_tier_storage_gb: float = 1000

    app_name: str = "Microscopy Pipeline"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def tier_limits(self) -> dict[str, float]:
        return {
            "free": self.free_tier_storage_gb,
            "pro": self.pro_tier_storage_gb,
            "enterprise": self.enterprise_tier_storage_gb,
        }

    def ensure_dirs(self) -> None:
        for path in (self.upload_folder, self.results_folder, self.models_folder):
            Path(path).mkdir(parents=True, exist_ok=True)
        # SQLite file dir
        if self.database_url.startswith("sqlite"):
            db_path = self.database_url.split("///")[-1]
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_dirs()
    return settings
