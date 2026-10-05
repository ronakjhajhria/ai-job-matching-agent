import logging

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from redis.exceptions import RedisError
from sqlalchemy.exc import SQLAlchemyError

from app.memory.preferences import (
    CandidatePreferenceRecord,
    CandidatePreferencesRepository,
    SearchPreferences,
)
from app.memory.session_store import ConversationMessage, RedisConversationStore

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Candidate Memory"])


class ConversationMessageRequest(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1, max_length=4000)


def _get_preference_repository(request: Request) -> CandidatePreferencesRepository:
    repository = getattr(request.app.state, "candidate_preferences", None)
    if repository is None:
        raise HTTPException(503, "Candidate preference storage is not configured.")
    return repository


def _get_session_store(request: Request) -> RedisConversationStore:
    store = getattr(request.app.state, "conversation_store", None)
    if store is None:
        raise HTTPException(503, "Conversation memory is not configured.")
    return store


@router.put(
    "/api/v1/preferences/{candidate_id}",
    response_model=CandidatePreferenceRecord,
)
def save_preferences(
    candidate_id: str,
    preferences: SearchPreferences,
    request: Request,
) -> CandidatePreferenceRecord:
    try:
        return _get_preference_repository(request).save(candidate_id, preferences)
    except SQLAlchemyError as error:
        logger.exception("Could not save candidate preferences")
        raise HTTPException(503, "Candidate preference storage is unavailable.") from error


@router.get(
    "/api/v1/preferences/{candidate_id}",
    response_model=CandidatePreferenceRecord,
)
def read_preferences(candidate_id: str, request: Request) -> CandidatePreferenceRecord:
    try:
        record = _get_preference_repository(request).get(candidate_id)
    except SQLAlchemyError as error:
        logger.exception("Could not load candidate preferences")
        raise HTTPException(503, "Candidate preference storage is unavailable.") from error
    if record is None:
        raise HTTPException(404, "Candidate preferences were not found.")
    return record


@router.post(
    "/api/v1/sessions/{session_id}/messages",
    response_model=list[ConversationMessage],
)
def append_session_message(
    session_id: str,
    payload: ConversationMessageRequest,
    request: Request,
) -> list[ConversationMessage]:
    message = ConversationMessage(role=payload.role, content=payload.content)
    try:
        return _get_session_store(request).append(session_id, message)
    except RedisError as error:
        logger.exception("Could not append conversation message")
        raise HTTPException(503, "Conversation memory is unavailable.") from error


@router.get(
    "/api/v1/sessions/{session_id}/messages",
    response_model=list[ConversationMessage],
)
def read_session_messages(session_id: str, request: Request) -> list[ConversationMessage]:
    try:
        return _get_session_store(request).get_recent(session_id)
    except RedisError as error:
        logger.exception("Could not load conversation messages")
        raise HTTPException(503, "Conversation memory is unavailable.") from error