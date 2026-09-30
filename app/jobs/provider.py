from typing import Protocol
from app.llm.schemas_intelligence import JobDescription

class JobProvider(Protocol):
    """Protocol for fetching available jobs."""
    def search_jobs(self, query: str, limit: int = 5) -> list[JobDescription]:
        ...

class MockJobProvider(JobProvider):
    """A local mock provider so the system works without API keys."""
    def __init__(self):
        self.jobs = [
            JobDescription(
                job_id="job-1",
                role="Backend Engineer",
                company="TechCorp",
                required_skills=["Python", "FastAPI", "Docker"],
                preferred_skills=["AWS", "Kubernetes"],
                responsibilities=["Build microservices", "Deploy to cloud"],
                experience_requirements="3+ years",
                education_requirements="B.S. Computer Science",
                location="Remote",
                technologies=["Python", "PostgreSQL"]
            ),
            JobDescription(
                job_id="job-2",
                role="Frontend Developer",
                company="WebStudio",
                required_skills=["React", "TypeScript", "CSS"],
                preferred_skills=["Figma"],
                responsibilities=["Build UI components"],
                experience_requirements="2+ years",
                education_requirements="None",
                location="New York",
                technologies=["React"]
            )
        ]

    def search_jobs(self, query: str, limit: int = 5) -> list[JobDescription]:
        # Simple naive keyword matching for mock
        results = []
        for job in self.jobs:
            if query.lower() in job.role.lower() or query.lower() in job.company.lower() or any(query.lower() in s.lower() for s in job.required_skills):
                results.append(job)
        return results[:limit]
