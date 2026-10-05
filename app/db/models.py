from datetime import UTC, datetime

from sqlalchemy import DateTime, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CandidatePreferencesRow(Base):
    __tablename__ = "candidate_preferences"

    candidate_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    preferences: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )