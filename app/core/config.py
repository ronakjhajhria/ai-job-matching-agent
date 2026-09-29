"""Validated application settings loaded from the environment."""

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings can be supplied as JOBMIND_* variables or in a local .env file."""

    model_config = SettingsConfigDict(
        env_prefix="JOBMIND_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    service_name: str = "JobMind"
    environment: Literal["development", "test", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"