# JobMind — Agentic AI Career Intelligence Platform

> A production-style portfolio project demonstrating RAG, LLM structured output, semantic matching, and LangGraph agent orchestration — built for an SDE/AI/ML internship portfolio.

---

## Architecture

```
                 ┌─────────────────┐
                 │      User       │
                 └────────┬────────┘
                          ↓
                 ┌─────────────────┐
                 │    FastAPI      │  (Phases 1, 14)
                 └────────┬────────┘
                          ↓
                 ┌─────────────────┐
                 │ LangGraph Agent │  (Phase 8)
                 └────────┬────────┘
                          ↓
          ┌───────────────┼────────────────┐
          ↓               ↓                ↓
   Resume RAG        Job Search       Skill Analyzer
   (Phase 4)         (Phase 9)        (Phase 2/7)
          ↓               ↓                ↓
       Qdrant        Job Provider      LLM/Pydantic
   (Phase 3)       (Mock/API)       (Phase 2/5/6/7)
          └───────────────┼────────────────┘
                          ↓
                  ┌──────────────┐
                  │     LLM      │  OpenAI / any provider
                  └──────┬───────┘
                         ↓
                 Answer + Citations
```

## Repository Structure

```
jobmind/
├── app/
│   ├── api/routes/         # FastAPI route handlers
│   │   ├── agent.py        # Phase 8: LangGraph agent endpoint
│   │   ├── intelligence.py # Phase 5/6: Resume & JD parsing
│   │   ├── matching.py     # Phase 7: Semantic job matching
│   │   ├── rag.py          # Phase 4: RAG Q&A with citations
│   │   ├── skills.py       # Phase 2: Skill extraction
│   │   └── tracker.py      # Phase 11: Application tracker
│   ├── agents/
│   │   └── career_agent.py # Phase 8: LangGraph graph definition
│   ├── core/
│   │   ├── config.py       # Pydantic settings (JOBMIND_* env vars)
│   │   └── logging_config.py
│   ├── documents/
│   │   ├── parser.py       # Phase 3: PDF/TXT text extraction
│   │   └── chunker.py      # Phase 3: Sliding-window chunker
│   ├── embeddings/
│   │   ├── provider.py     # EmbeddingsProvider protocol
│   │   └── openai_provider.py
│   ├── guardrails/
│   │   └── input_guard.py  # Phase 13: Injection detection, PII redaction
│   ├── jobs/
│   │   └── provider.py     # Phase 9: JobProvider protocol + Mock
│   ├── llm/
│   │   ├── provider.py     # LLMProvider protocol
│   │   ├── openai_provider.py
│   │   ├── prompts.py      # Prompt templates
│   │   ├── prompts_intelligence.py
│   │   ├── schemas.py      # SkillExtraction, RagResponse, Citation
│   │   └── schemas_intelligence.py  # ResumeProfile, JobDescription, JobMatchResult
│   ├── matching/
│   │   └── analyzer.py     # Phase 5/6/7: CareerAnalyzer
│   ├── memory/
│   │   └── tracker.py      # Phase 11: ApplicationTracker
│   ├── rag/
│   │   ├── ingestion.py    # Phase 3: IngestionPipeline
│   │   ├── retriever.py    # Phase 4: Retriever
│   │   └── generator.py    # Phase 4: RAGAnswerGenerator
│   ├── vectorstore/
│   │   └── qdrant_store.py # Qdrant wrapper (in-memory or URL)
│   └── main.py             # Application factory
├── evaluation/
│   ├── rag_eval.py         # Phase 12: Recall@K, Source Hit Rate
│   └── run.py              # Entry point: python -m evaluation.run
├── tests/                  # pytest test suite
├── docs/
│   ├── concepts.md         # Design decisions per phase
│   └── interview.md        # Interview Q&A per phase
├── Dockerfile
├── docker-compose.yml      # API + Qdrant
├── .github/workflows/ci.yml
├── .env.example
└── pyproject.toml
```

## Requirements

- Python 3.11+
- OpenAI API key (for LLM + embedding endpoints)

## Quick Start (Local)

```bash
# 1. Clone & enter the repo
git clone https://github.com/your-username/jobmind.git
cd jobmind

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -e ".[dev]"

# 4. Configure environment
cp .env.example .env
# Edit .env and set JOBMIND_OPENAI_API_KEY=sk-...

# 5. Run the API
uvicorn app.main:app --reload
```

Open http://localhost:8000/docs for the interactive API docs.

## Quick Start (Docker)

```bash
cp .env.example .env
# Edit .env and set JOBMIND_OPENAI_API_KEY=sk-...
# Also set JOBMIND_QDRANT_URL=http://qdrant:6333

docker compose up --build
```

## API Endpoints

| Method | Path | Phase | Description |
|--------|------|-------|-------------|
| GET | `/health` | 1 | Liveness check |
| POST | `/api/v1/skills/extract` | 2 | Extract skills from text |
| POST | `/api/v1/rag/ask` | 4 | RAG Q&A with citations |
| POST | `/api/v1/intelligence/parse/resume` | 5 | Parse resume to structured JSON |
| POST | `/api/v1/intelligence/parse/job` | 6 | Parse job description to structured JSON |
| POST | `/api/v1/matching/analyze` | 7 | Semantic skill-gap analysis |
| POST | `/api/v1/agent/ask` | 8 | LangGraph career agent |
| POST | `/api/v1/tracker/update` | 11 | Track a job application |
| GET | `/api/v1/tracker/list` | 11 | List applications (filter by status) |

## Example Requests

**Skill Extraction**
```bash
curl -X POST http://localhost:8000/api/v1/skills/extract \
  -H "Content-Type: application/json" \
  -d '{"text": "Built REST APIs with Python/FastAPI, deployed on AWS with Docker."}'
```

**Agent**
```bash
curl -X POST http://localhost:8000/api/v1/agent/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "Find backend jobs that match my resume and tell me what skills I am missing."}'
```

**Job Match**
```bash
curl -X POST http://localhost:8000/api/v1/matching/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "resume_text": "3 years Python, FastAPI, Docker experience.",
    "job_description_text": "Looking for a Python backend engineer with Kubernetes experience."
  }'
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=term-missing
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `JOBMIND_OPENAI_API_KEY` | unset | Required for all LLM/RAG features |
| `JOBMIND_OPENAI_MODEL` | `gpt-4o-mini` | LLM model |
| `JOBMIND_OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model |
| `JOBMIND_EMBEDDING_VECTOR_SIZE` | `1536` | Must match embedding model dimension |
| `JOBMIND_QDRANT_URL` | `:memory:` | Qdrant host (`:memory:` for local dev) |
| `JOBMIND_QDRANT_COLLECTION` | `jobmind_docs` | Collection name in Qdrant |
| `JOBMIND_CHUNK_SIZE` | `1000` | Characters per document chunk |
| `JOBMIND_CHUNK_OVERLAP` | `200` | Character overlap between chunks |
| `JOBMIND_ENVIRONMENT` | `development` | `development`, `test`, `production` |
| `JOBMIND_LOG_LEVEL` | `INFO` | Log level |

## Interview Resources

See [`docs/concepts.md`](docs/concepts.md) for architecture decisions and [`docs/interview.md`](docs/interview.md) for likely interview questions and answers, organized by phase.
