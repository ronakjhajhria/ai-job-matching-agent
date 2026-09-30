def skill_extraction_messages(text: str) -> list[dict[str, str]]:
    """Build the prompt messages for extracting skills from a document."""
    return [
        {
            "role": "system",
            "content": (
                "You are an expert technical recruiter and career intelligence AI. "
                "Your task is to analyze the provided text (which may be a resume or job description) "
                "and extract explicitly mentioned skills, technologies, and core competencies. "
                "Do NOT infer or hallucinate skills that are not supported by the text. "
                "Return the extracted skills and a brief 1-2 sentence summary of the person's or job's focus."
            )
        },
        {
            "role": "user",
            "content": f"Please extract the skills and summary from the following text:\n\n{text}"
        }
    ]

def rag_qa_messages(query: str, context: str) -> list[dict[str, str]]:
    """Build the prompt messages for Retrieval-Augmented Generation."""
    return [
        {
            "role": "system",
            "content": (
                "You are an intelligent career assistant. You will be provided with a user's question "
                "and several retrieved context chunks from their resume or job descriptions.\n\n"
                "RULES:\n"
                "1. You MUST answer the question using ONLY the provided context.\n"
                "2. If the answer is not contained in the context, you must state that you do not have enough information.\n"
                "3. You MUST provide exact citations for your claims, referencing the source document name and quoting the text."
            )
        },
        {
            "role": "user",
            "content": f"CONTEXT:\n{context}\n\nQUESTION:\n{query}"
        }
    ]
