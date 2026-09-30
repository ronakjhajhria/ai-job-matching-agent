from pydantic import BaseModel, Field

# Phase 5: Resume Intelligence
class ResumeProfile(BaseModel):
    """Structured extraction of a user's resume."""
    name: str = Field(description="Full name of the candidate")
    education: list[str] = Field(description="List of degrees and institutions")
    skills: list[str] = Field(description="Technical and soft skills")
    projects: list[str] = Field(description="Notable projects")
    experience: list[str] = Field(description="Past job titles and companies")
    achievements: list[str] = Field(description="Key quantifiable achievements")
    preferred_roles: list[str] = Field(description="Roles the candidate seems best suited for")

# Phase 6: Job Description Intelligence
class JobDescription(BaseModel):
    """Structured extraction of a job posting."""
    job_id: str = Field(description="A unique identifier for the job (generate one if missing)")
    role: str = Field(description="Job title")
    company: str = Field(description="Hiring company")
    required_skills: list[str] = Field(description="Must-have skills")
    preferred_skills: list[str] = Field(description="Nice-to-have skills")
    responsibilities: list[str] = Field(description="Key day-to-day duties")
    experience_requirements: str = Field(description="Years of experience needed")
    education_requirements: str = Field(description="Degrees needed")
    location: str = Field(description="Job location or remote status")
    technologies: list[str] = Field(description="Tech stack mentioned")

# Phase 7: Semantic Job Matching
class JobMatchResult(BaseModel):
    """Result of comparing a Resume to a Job Description."""
    match_score_1_to_10: int = Field(description="Overall match score from 1 to 10")
    matching_skills: list[str] = Field(description="Skills both the candidate and job share")
    missing_skills: list[str] = Field(description="Required skills the candidate lacks")
    related_skills: list[str] = Field(description="Skills the candidate has that are closely related to requirements")
    evidence_from_resume: list[str] = Field(description="Quotes from resume proving qualifications")
    evidence_from_jd: list[str] = Field(description="Quotes from JD mapping to the candidate's strengths")
    explanation: str = Field(description="A holistic explanation of why they are or aren't a good fit")
