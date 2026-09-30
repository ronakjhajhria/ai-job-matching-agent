"""Phase 8 API: LangGraph Agent endpoint."""

import logging
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.guardrails.input_guard import check_input

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/agent", tags=["Agent"])


class AgentRequest(BaseModel):
    query: str = Field(min_length=3, max_length=1000)


class AgentResponse(BaseModel):
    answer: str
    tools_used: list[str]


@router.post("/ask", response_model=AgentResponse)
def agent_ask(payload: AgentRequest, request: Request) -> AgentResponse:
    """
    Submit a question to the LangGraph career agent.
    The agent autonomously decides which tools (resume_retriever, job_search,
    skill_analyzer) to call based on your question.
    """
    # Phase 13: run guardrails
    guard_result = check_input(payload.query)
    if not guard_result.is_safe:
        raise HTTPException(
            status_code=400,
            detail=f"Input rejected by guardrails: {'; '.join(guard_result.reasons)}"
        )

    agent_graph = getattr(request.app.state, "agent_graph", None)
    if not agent_graph:
        raise HTTPException(503, "Agent is not initialized.")

    try:
        initial_state = {
            "query": guard_result.sanitized_text,
            "tool_calls_made": [],
            "resume_context": "",
            "job_results": [],
            "skill_analysis": "",
            "final_answer": "",
            "error": None,
            "iteration_count": 0,
        }
        result = agent_graph.invoke(initial_state)
        return AgentResponse(
            answer=result.get("final_answer", "No answer generated."),
            tools_used=result.get("tool_calls_made", [])
        )
    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        raise HTTPException(500, "Agent execution failed.")
