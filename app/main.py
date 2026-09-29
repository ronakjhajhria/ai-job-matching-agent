"""FastAPI application entry point."""

from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel

from app.core.config import Settings
from app.core.logging_config import configure_logging


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the API with explicit settings, defaulting to environment config."""
    app_settings = settings or Settings()
    configure_logging(app_settings.log_level)

    application = FastAPI(title=app_settings.service_name)

    @application.get("/health", response_model=HealthResponse, tags=["health"])
    async def health() -> HealthResponse:
        return HealthResponse(status="ok", service=app_settings.service_name)

    return application


app = create_app()