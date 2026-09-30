"""
JobMind — FastAPI application entry point.

Builds every subsystem and wires them together:
  Phase 1  — FastAPI + health
  Phase 2  — LLM provider (OpenAI)
  Phase 3  — Document ingestion (parser, chunker, Qdrant)
  Phase 4  — RAG generator
  Phase 5/6 — Intelligence routes (resume & JD parsing)
  Phase 7  — Matching route
  Phase 8  — LangGraph agent
  Phase 9  — Job provider (Mock by default)
  Phase 11 — Application tracker
"""

from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel

from app.core.config import Settings
from app.core.logging_config import configure_logging

# Routers
from app.api.routes.skills import router as skills_router
from app.api.routes.rag import router as rag_router
from app.api.routes.intelligence import router as intelligence_router
from app.api.routes.matching import router as matching_router
from app.api.routes.tracker import router as tracker_router
from app.api.routes.agent import router as agent_router

# LLM
from app.llm.provider import LLMProvider
from app.llm.openai_provider import OpenAIProvider

# Embeddings & Vector Store
from app.embeddings.openai_provider import OpenAIEmbeddingsProvider
from app.vectorstore.qdrant_store import QdrantStore

# RAG
from app.rag.retriever import Retriever
from app.rag.generator import RAGAnswerGenerator

# Agent
from app.agents.career_agent import build_agent_graph

# Jobs & Memory
from app.jobs.provider import MockJobProvider
from app.memory.tracker import ApplicationTracker


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    environment: str
    llm_configured: bool
    rag_configured: bool
    agent_configured: bool


def create_app(
    settings: Settings | None = None,
    llm_provider: LLMProvider | None = None,
    rag_generator: RAGAnswerGenerator | None = None,
    agent_graph=None,
) -> FastAPI:
    """
    Build the JobMind application.
    All external dependencies are injectable, making every component testable.
    """
    s = settings or Settings()
    configure_logging(s.log_level)

    app = FastAPI(
        title=s.service_name,
        description="Agentic AI Career Intelligence Platform",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ------------------------------------------------------------------ #
    # Resolve API key once
    # ------------------------------------------------------------------ #
    api_key: str | None = s.openai_api_key.get_secret_value() if s.openai_api_key else None

    # ------------------------------------------------------------------ #
    # Phase 2 — LLM Provider
    # ------------------------------------------------------------------ #
    if llm_provider is None and api_key:
        llm_provider = OpenAIProvider(
            api_key=api_key,
            model=s.openai_model,
            timeout=s.llm_timeout_seconds,
            max_retries=s.llm_max_retries,
        )
    app.state.llm_provider = llm_provider

    # ------------------------------------------------------------------ #
    # Phase 3 & 4 — Embeddings, VectorStore, RAG
    # ------------------------------------------------------------------ #
    retriever: Retriever | None = None
    if rag_generator is None and api_key and llm_provider:
        embeddings = OpenAIEmbeddingsProvider(
            api_key=api_key,
            model=s.openai_embedding_model,
        )
        vector_store = QdrantStore(
            collection_name=s.qdrant_collection,
            embeddings=embeddings,
            vector_size=s.embedding_vector_size,
        )
        retriever = Retriever(vector_store=vector_store, embeddings=embeddings)
        rag_generator = RAGAnswerGenerator(llm_provider=llm_provider, retriever=retriever)

    app.state.rag_generator = rag_generator

    # ------------------------------------------------------------------ #
    # Phase 8 & 9 — LangGraph Agent + Job Provider
    # ------------------------------------------------------------------ #
    job_provider = MockJobProvider()
    app.state.job_provider = job_provider

    if agent_graph is None and llm_provider and retriever:
        agent_graph = build_agent_graph(
            llm=llm_provider,
            retriever=retriever,
            job_provider=job_provider,
        )
    app.state.agent_graph = agent_graph

    # ------------------------------------------------------------------ #
    # Phase 11 — Application Tracker
    # ------------------------------------------------------------------ #
    app.state.tracker = ApplicationTracker()

    # ------------------------------------------------------------------ #
    # Routes
    # ------------------------------------------------------------------ #
    @app.get("/health", response_model=HealthResponse, tags=["System"])
    async def health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            service=s.service_name,
            environment=s.environment,
            llm_configured=app.state.llm_provider is not None,
            rag_configured=app.state.rag_generator is not None,
            agent_configured=app.state.agent_graph is not None,
        )

    app.include_router(skills_router)
    app.include_router(rag_router)
    app.include_router(intelligence_router)
    app.include_router(matching_router)
    app.include_router(tracker_router)
    app.include_router(agent_router)

    return app


# ASGI entry point
app = create_app()
