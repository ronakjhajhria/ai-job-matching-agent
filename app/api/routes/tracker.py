"""Phase 11 API: Application Tracker memory endpoints."""

import logging
from fastapi import APIRouter, HTTPException, Request

from app.memory.tracker import ApplicationRecord, ApplicationTracker

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/tracker", tags=["Application Tracker"])


def _get_tracker(request: Request) -> ApplicationTracker:
    tracker = getattr(request.app.state, "tracker", None)
    if not tracker:
        raise HTTPException(503, "Application tracker is not initialized.")
    return tracker


@router.post("/update", response_model=ApplicationRecord)
def update_application(payload: ApplicationRecord, request: Request) -> ApplicationRecord:
    """Add or update a job application in the tracker."""
    tracker = _get_tracker(request)
    tracker.applications[payload.job_id] = payload
    return payload


@router.get("/list", response_model=list[ApplicationRecord])
def list_applications(
    request: Request,
    status: str | None = None
) -> list[ApplicationRecord]:
    """List all tracked applications, optionally filtered by status."""
    tracker = _get_tracker(request)
    return tracker.get_applications(status=status)
