"""
PHASE 8: LangGraph Agent System

LangGraph is a library that lets you build stateful multi-step agents as graphs.
Each node in the graph is a function that reads/writes to a shared State object.
The agent decides which tools to call based on the user's query, executes them,
and loops until it can produce a final answer.

WHY LANGGRAPH:
- State machine approach prevents infinite loops (unlike raw ReAct loops)
- Tools are explicit and typed (no random tool calls)
- Easy to add retries, error recovery, and termination conditions
"""

from typing import TypedDict, Annotated
import operator
import json
import logging

from langgraph.graph import StateGraph, END

from app.llm.provider import LLMProvider
from app.jobs.provider import JobProvider
from app.rag.retriever import Retriever
from app.matching.analyzer import CareerAnalyzer
from app.memory.tracker import ApplicationTracker

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# 1. AGENT STATE
# Shared state object that flows through every node in the graph.
# --------------------------------------------------------------------------- #
class AgentState(TypedDict):
    query: str                          # The user's question
    tool_calls_made: list[str]          # Which tools have already been called
    resume_context: str                 # Retrieved resume chunks
    job_results: list[dict]             # Job search results
    skill_analysis: str                 # Output from skill analyzer tool
    final_answer: str                   # The final response to the user
    error: str | None                   # Any error message
    iteration_count: int                # Guard against infinite loops


MAX_ITERATIONS = 5  # Phase 13 guardrail

# --------------------------------------------------------------------------- #
# 2. ROUTER — Decides which tool to call next
# --------------------------------------------------------------------------- #
def route_query(state: AgentState) -> str:
    """
    Simple rule-based router: decides the next tool based on the query 
    and which tools have already been called.
    
    In a more advanced version, this would call the LLM itself for planning.
    We keep it explicit to avoid random tool calls (per project rules).
    """
    if state["iteration_count"] >= MAX_ITERATIONS:
        return "finalize"

    query_lower = state["query"].lower()
    called = set(state.get("tool_calls_made", []))

    # If we need resume info and haven't retrieved it yet
    resume_keywords = ["resume", "experience", "skills", "background", "qualification"]
    if any(kw in query_lower for kw in resume_keywords) and "resume_retriever" not in called:
        return "resume_retriever"

    # If we need jobs and haven't searched yet
    job_keywords = ["job", "role", "position", "apply", "find", "suitable", "match"]
    if any(kw in query_lower for kw in job_keywords) and "job_search" not in called:
        return "job_search"

    # If we have both resume and jobs, do skill analysis
    if "resume_retriever" in called and "job_search" in called and "skill_analyzer" not in called:
        return "skill_analyzer"

    # Otherwise finalize
    return "finalize"


# --------------------------------------------------------------------------- #
# 3. TOOL NODES
# --------------------------------------------------------------------------- #
def build_resume_retriever_node(retriever: Retriever):
    def resume_retriever_node(state: AgentState) -> dict:
        logger.info("Agent: calling resume_retriever tool")
        try:
            chunks = retriever.retrieve(state["query"], top_k=4)
            context = "\n\n".join(c.text for c in chunks)
            called = state.get("tool_calls_made", []) + ["resume_retriever"]
            return {
                "resume_context": context or "No resume content found.",
                "tool_calls_made": called,
                "iteration_count": state["iteration_count"] + 1,
            }
        except Exception as e:
            logger.error(f"resume_retriever failed: {e}")
            return {"error": str(e), "iteration_count": state["iteration_count"] + 1}
    return resume_retriever_node


def build_job_search_node(job_provider: JobProvider):
    def job_search_node(state: AgentState) -> dict:
        logger.info("Agent: calling job_search tool")
        try:
            jobs = job_provider.search_jobs(state["query"], limit=5)
            called = state.get("tool_calls_made", []) + ["job_search"]
            return {
                "job_results": [j.model_dump() for j in jobs],
                "tool_calls_made": called,
                "iteration_count": state["iteration_count"] + 1,
            }
        except Exception as e:
            logger.error(f"job_search failed: {e}")
            return {"error": str(e), "iteration_count": state["iteration_count"] + 1}
    return job_search_node


def build_skill_analyzer_node(llm: LLMProvider):
    from app.llm.schemas import SkillExtraction
    from app.llm.prompts import skill_extraction_messages

    def skill_analyzer_node(state: AgentState) -> dict:
        logger.info("Agent: calling skill_analyzer tool")
        try:
            # Combine resume context and job results for comparison
            job_skills = []
            for job in state.get("job_results", []):
                job_skills.extend(job.get("required_skills", []))

            text = f"Resume:\n{state['resume_context']}\n\nJob Required Skills: {', '.join(set(job_skills))}"
            extraction = llm.generate_structured(skill_extraction_messages(text[:4000]), SkillExtraction)
            called = state.get("tool_calls_made", []) + ["skill_analyzer"]
            return {
                "skill_analysis": extraction.summary,
                "tool_calls_made": called,
                "iteration_count": state["iteration_count"] + 1,
            }
        except Exception as e:
            logger.error(f"skill_analyzer failed: {e}")
            return {"error": str(e), "iteration_count": state["iteration_count"] + 1}
    return skill_analyzer_node


def finalize_node(state: AgentState) -> dict:
    """Synthesize all collected info into a final answer."""
    logger.info("Agent: finalizing answer")
    
    if state.get("error"):
        return {"final_answer": f"I encountered an error: {state['error']}"}

    parts = [f"**Your question:** {state['query']}\n"]

    if state.get("resume_context"):
        parts.append(f"**Resume context retrieved.**\n")

    if state.get("job_results"):
        jobs = state["job_results"]
        job_lines = [f"- {j['role']} at {j['company']} (required: {', '.join(j.get('required_skills', []))})" for j in jobs]
        parts.append("**Matching jobs found:**\n" + "\n".join(job_lines))

    if state.get("skill_analysis"):
        parts.append(f"\n**Skill Analysis:**\n{state['skill_analysis']}")

    if len(parts) == 1:  # No tools were called
        parts.append("Based on your query, no specific tools were needed. Please ask about your resume, skills, or job search.")

    return {"final_answer": "\n\n".join(parts)}


# --------------------------------------------------------------------------- #
# 4. BUILD THE GRAPH
# --------------------------------------------------------------------------- #
def build_agent_graph(
    llm: LLMProvider,
    retriever: Retriever,
    job_provider: JobProvider,
) -> StateGraph:
    """
    Construct the LangGraph workflow.
    
    Graph structure:
        START -> router -> [resume_retriever | job_search | skill_analyzer | finalize]
        Each tool node feeds back to the router (loop until finalize).
    """
    graph = StateGraph(AgentState)

    # Register nodes
    graph.add_node("resume_retriever", build_resume_retriever_node(retriever))
    graph.add_node("job_search", build_job_search_node(job_provider))
    graph.add_node("skill_analyzer", build_skill_analyzer_node(llm))
    graph.add_node("finalize", finalize_node)

    # Entry point: route_query decides first step
    graph.set_conditional_entry_point(
        route_query,
        {
            "resume_retriever": "resume_retriever",
            "job_search": "job_search",
            "skill_analyzer": "skill_analyzer",
            "finalize": "finalize",
        }
    )

    # After each tool, re-route (loop)
    for node in ["resume_retriever", "job_search", "skill_analyzer"]:
        graph.add_conditional_edges(
            node,
            route_query,
            {
                "resume_retriever": "resume_retriever",
                "job_search": "job_search",
                "skill_analyzer": "skill_analyzer",
                "finalize": "finalize",
            }
        )

    graph.add_edge("finalize", END)

    return graph.compile()
