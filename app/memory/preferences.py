from datetime import UTC, datetime
from typing import Protocol

from pydantic import BaseModel, Field, model_validator
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import CandidatePreferencesRow


class SearchPreferences(BaseModel):
    preferred_roles: list[str] = Field(default_factory=list, max_length=20)
    skills: list[str] = Field(default_factory=list, max_length=100)
    locations: list[str] = Field(default_factory=list, max_length=30)
    remote_only: bool | None = None
    min_years_experience: float | None = Field(default=None, ge=0, le=80)
    min_salary: int | None = Field(default=None, ge=0)
    max_salary: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def salary_range_is_valid(self) -> "SearchPreferences":
        if (
            self.min_salary is not None
            and self.max_salary is not None
            and self.min_salary > self.max_salary
        ):
            raise ValueError("min_salary must be less than or equal to max_salary")
        return self


class CandidatePreferenceRecord(BaseModel):
    candidate_id: str
    preferences: SearchPreferences
    updated_at: datetime


class CandidatePreferencesRepository(Protocol):
    def get(self, candidate_id: str) -> CandidatePreferenceRecord | None:
        ...

    def save(
        self, candidate_id: str, preferences: SearchPreferences
    ) -> CandidatePreferenceRecord:
        ...


class SqlCandidatePreferencesRepository:
    def __init__(self, session_factory: sessionmaker[Session]):
        self.session_factory = session_factory

    def get(self, candidate_id: str) -> CandidatePreferenceRecord | None:
        with self.session_factory() as session:
            row = session.get(CandidatePreferencesRow, candidate_id)
            if row is None:
                return None
            return self._to_record(row)

    def save(
        self, candidate_id: str, preferences: SearchPreferences
    ) -> CandidatePreferenceRecord:
        with self.session_factory.begin() as session:
            row = session.get(CandidatePreferencesRow, candidate_id)
            payload = preferences.model_dump(mode="json")

            if row is None:
                row = CandidatePreferencesRow(
                    candidate_id=candidate_id,
                    preferences=payload,
                    updated_at=datetime.now(UTC),
                )
                session.add(row)
            else:
                row.preferences = payload
                row.updated_at = datetime.now(UTC)

            return CandidatePreferenceRecord(
                candidate_id=row.candidate_id,
                preferences=SearchPreferences.model_validate(row.preferences),
                updated_at=row.updated_at,
            )

    @staticmethod
    def _to_record(row: CandidatePreferencesRow) -> CandidatePreferenceRecord:
        return CandidatePreferenceRecord(
            candidate_id=row.candidate_id,
            preferences=SearchPreferences.model_validate(row.preferences),
            updated_at=row.updated_at,
        )