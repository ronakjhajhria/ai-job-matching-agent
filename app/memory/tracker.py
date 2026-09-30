from pydantic import BaseModel
from datetime import datetime

class ApplicationRecord(BaseModel):
    job_id: str
    company: str
    role: str
    status: str # "applied", "interview", "rejected", "offer", "saved"
    date_updated: datetime
    notes: str = ""

class ApplicationTracker:
    """Basic persistent memory for tracking job applications."""
    def __init__(self):
        # In a real app, this would use a database (SQLite/Postgres)
        self.applications: dict[str, ApplicationRecord] = {}

    def update_status(self, job_id: str, company: str, role: str, status: str, notes: str = "") -> ApplicationRecord:
        record = ApplicationRecord(
            job_id=job_id,
            company=company,
            role=role,
            status=status,
            date_updated=datetime.utcnow(),
            notes=notes
        )
        self.applications[job_id] = record
        return record

    def get_applications(self, status: str | None = None) -> list[ApplicationRecord]:
        if status:
            return [app for app in self.applications.values() if app.status == status]
        return list(self.applications.values())
