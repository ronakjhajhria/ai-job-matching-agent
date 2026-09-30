from app.llm.provider import LLMProvider
from app.llm.schemas_intelligence import ResumeProfile, JobDescription, JobMatchResult
from app.llm.prompts_intelligence import parse_resume_messages, parse_job_messages, match_job_messages

class CareerAnalyzer:
    """Handles extracting and matching resumes and job descriptions."""
    
    def __init__(self, llm: LLMProvider):
        self.llm = llm

    def parse_resume(self, text: str) -> ResumeProfile:
        messages = parse_resume_messages(text)
        return self.llm.generate_structured(messages, ResumeProfile)

    def parse_job(self, text: str) -> JobDescription:
        messages = parse_job_messages(text)
        return self.llm.generate_structured(messages, JobDescription)

    def match_profiles(self, resume: ResumeProfile, job: JobDescription) -> JobMatchResult:
        # Convert Pydantic models to JSON strings for the prompt
        messages = match_job_messages(
            resume_profile=resume.model_dump_json(indent=2),
            job_profile=job.model_dump_json(indent=2)
        )
        return self.llm.generate_structured(messages, JobMatchResult)
