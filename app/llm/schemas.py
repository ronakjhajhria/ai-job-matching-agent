from pydantic import BaseModel, Field

class SkillExtraction(BaseModel):
    """Structured output schema for skill extraction."""
    skills: list[str] = Field(
        description="List of technical and professional skills extracted from the text."
    )
    summary: str = Field(
        description="A brief 1-2 sentence summary of the person's core expertise or the job's core requirements."
    )

class Citation(BaseModel):
    """Represents a specific source reference used to generate an answer."""
    source_document: str = Field(description="The name of the source document (e.g., 'resume.pdf')")
    exact_quote: str = Field(description="A short, exact quote from the document supporting the answer")

class RagResponse(BaseModel):
    """Structured response for RAG-based Q&A."""
    answer: str = Field(description="The final answer to the user's question, strictly based on the provided context.")
    citations: list[Citation] = Field(description="List of citations proving where the answer came from.")

