# Concepts

## Phase 1: Project Foundation

### What this component does
We established the core skeleton of the JobMind API. This includes the FastAPI web server, configuration management via environment variables, basic logging, a health check endpoint, and unit testing.

### Why it exists
A robust foundation ensures that as we add complex LLM and RAG logic in later phases, the application remains testable, configurable, and easy to deploy.

### Important Design Decisions
1. **Application Factory (`create_app`)**: Instead of creating a global `app = FastAPI()` that hardcodes settings, we use a factory function. This allows us to inject different configurations (like a testing environment) during tests without mutating global state.
2. **Pydantic Settings**: We use `pydantic-settings` to load configuration from environment variables (prefixed with `JOBMIND_`). This provides strict type validation (e.g., failing at startup if an invalid log level is provided) rather than throwing cryptic errors later.
3. **Standard-Library Logging**: We configured Python's built-in `logging` module. Centralized structured logging is avoided for now to keep dependencies minimal until a production deployment requires it.

### Alternatives Considered
- **Flask or Django instead of FastAPI**: FastAPI was chosen because of its native async support and automatic OpenAPI (Swagger) documentation, which is highly beneficial for API-driven agent architectures.
- **Using `os.environ` directly**: While this avoids the `pydantic-settings` dependency, it pushes type coercion and validation logic into the application code, which becomes messy as the config grows.

### Limitations
The `/health` endpoint only verifies that the FastAPI process is running. It does not yet check the availability of external dependencies like Qdrant or the OpenAI API, as those components are not yet integrated.

## Phase 2: LLM Fundamentals & Structured Output

### What this component does
We implemented a robust abstraction layer for communicating with Large Language Models (LLMs) and created a working `/api/v1/skills/extract` endpoint. This endpoint takes text and uses the LLM to extract a structured list of skills and a summary.

### Why it exists
Directly calling the OpenAI SDK in our route handlers creates tight coupling. By creating an `LLMProvider` protocol, we can swap between OpenAI, Anthropic, or local models in the future without changing our business logic.

### Important Design Decisions
1. **Provider Protocol (`LLMProvider`)**: Defines the interface for generating structured data.
2. **Pydantic Validation**: We pass a Pydantic model (`SkillExtraction`) to the LLM. The OpenAI `beta.chat.completions.parse` method guarantees that the output strictly adheres to our JSON schema, returning a strongly-typed object.
3. **Dependency Injection via `app.state`**: The configured provider is stored on `request.app.state`. During testing, we inject a `MockLLMProvider` so our unit tests run instantly without requiring real network calls or an OpenAI API key.

### Alternatives Considered
- **LangChain / LlamaIndex**: We explicitly avoided these heavy orchestration frameworks for this phase. Our current requirement is a single LLM call with structured output, which the OpenAI SDK handles perfectly. Adding LangChain here would introduce unnecessary abstraction ("over-engineering") without solving a real workflow problem. We will introduce LangGraph later when we build complex multi-step agents.

### Limitations
The extraction quality depends entirely on the underlying model and the prompt. Currently, we do not verify if the extracted skills actually exist in the text (no hallucination checks), and we don't have protection against prompt-injection attacks.

## Phase 3: Resume/Document Ingestion

### What this component does
We built a document ingestion pipeline. It reads raw text from PDFs and TXT files, cleans erratic whitespace, splits the text into smaller overlapping "chunks," converts those chunks into mathematical vectors (embeddings), and stores them in a Qdrant Vector Database alongside metadata (like the source file name).

### Why it exists
LLMs have a context window limit. You cannot simply paste a 50-page document into a prompt. Even if you could, it degrades performance and increases latency/cost. By chunking documents and storing them as vectors, we set the foundation for Retrieval-Augmented Generation (RAG). Later, we can search this database to pull exactly the paragraphs we need to answer a user's question.

### Important Design Decisions
1. **Manual Chunking vs Framework Splitters**: We implemented `TextChunker` manually with a sliding window approach rather than importing LangChain's `RecursiveCharacterTextSplitter`. This demonstrates a fundamental understanding of how chunking logic actually works (advancing a window, stepping back for overlap, and respecting natural word boundaries).
2. **Qdrant Vector DB**: Qdrant was chosen because it's written in Rust (extremely fast), has a great Python client, and supports local in-memory storage for easy development while easily scaling to a Dockerized/Cloud instance for production.
3. **Embeddings Provider Abstraction**: Just like our `LLMProvider`, we abstracted `EmbeddingsProvider`. We can use OpenAI's embeddings (`text-embedding-3-small`) or swap to a local, free model like `sentence-transformers` without changing the ingestion pipeline.

### Limitations
- The PDF extraction uses `pypdf`, which extracts plain text but loses complex spatial layouts (like tables or multi-column resumes). Advanced OCR might be needed for highly stylized resumes.
- The text chunker uses string length. Token-based chunking (e.g., using `tiktoken`) would be strictly more accurate for aligning with LLM token limits, but string length is sufficient and computationally cheaper for a prototype.

## Phase 4: Retrieval-Augmented Generation (RAG)

### What this component does
We built the retrieval and generation pipeline. When a user asks a question, the system converts the question into an embedding vector, searches the Qdrant database for the most similar document chunks, formats those chunks into a prompt, and asks the LLM to answer the question *only* using those chunks. It also forces the LLM to provide citations.

### Why it exists
LLMs hallucinate. By forcing the model to rely strictly on retrieved context and provide citations (the exact source document and a quote), we ground the LLM's answers in reality. This is crucial for a career intelligence platform—if the system says a user is a match for a job, it must prove exactly why based on the resume.

### Important Design Decisions
1. **Separation of Concerns**: The `Retriever` handles embedding the query and querying Qdrant. The `RAGAnswerGenerator` handles formatting the retrieved context and calling the `LLMProvider`. This keeps our RAG pipeline decoupled and easily testable.
2. **Citation Schema**: We added `Citation` to our Pydantic schemas. This forces the LLM to output a JSON object containing `source_document` and `exact_quote`, making it easy for the frontend to render clickable citations.
3. **Retrieval Failure Handling**: If the retriever finds 0 results, the system short-circuits and immediately returns a polite failure message without calling the LLM. This saves money and latency.

### Alternatives Considered
- **Vector Search vs Keyword Search (BM25)**: We used pure vector search (Semantic Search). While powerful, it can sometimes struggle with exact keyword matching (like a specific acronym). In a more advanced iteration, we could implement Hybrid Search (combining Dense Vectors with Sparse Vectors/BM25) natively supported by Qdrant.

## Phase 5 & 6: Resume & Job Description Intelligence

### What it does
Parses raw text from a resume or job posting into a strongly-typed Pydantic schema using an LLM. This gives the system a structured understanding it can compare programmatically.

### Key Decisions
- **LLM over regex/NLP**: Resume parsing with regex fails on format variation. LLMs generalize well. Structured outputs guarantee schema compliance.
- **Separate schemas**: `ResumeProfile` and `JobDescription` are intentionally different shapes — resumes describe people, JDs describe roles.

## Phase 7: Semantic Job Matching

### What it does
Takes parsed `ResumeProfile` and `JobDescription`, feeds both as JSON to the LLM, and gets back a `JobMatchResult` with match score, evidence, gaps, and explanation.

### Key Decisions
- **LLM comparison over cosine similarity alone**: Simple skill set intersection misses related/adjacent skills (e.g. "REST APIs" vs "FastAPI"). The LLM can reason about proximity.
- **Structured match output**: Score is 1–10 integer; citations are list of strings — forcing the model to be specific and auditable.

## Phase 8: LangGraph Agent

### What it does
A stateful graph-based agent that autonomously decides which tools to call (resume_retriever, job_search, skill_analyzer) based on the user's query. Uses LangGraph's `StateGraph` with conditional routing.

### Key Decisions
- **Rule-based router (not LLM planner)**: Tool selection is based on keyword matching in the query. This avoids nondeterminism and random tool calls — per project rules. A future version could use an LLM planner.
- **MAX_ITERATIONS guardrail**: The graph cannot loop more than 5 times. This prevents infinite agent loops (Phase 13).
- **State is a TypedDict**: Every piece of information (resume context, jobs, analysis) is a named field. Easy to debug and test.

## Phase 9: Job Provider

### What it does
A `JobProvider` protocol with a `MockJobProvider` implementation so the system works without any external job board API key.

### Key Decisions
- **Protocol + Mock first**: Application logic depends on the interface, not the implementation. To add a real job API later (e.g. JSearch via RapidAPI), just create `APIJobProvider(JobProvider)`.

## Phase 11: Application Tracker

### What it does
In-memory tracker for job applications with status (applied, interview, rejected, offer, saved). Exposed via REST API.

### Key Decisions
- **Separate from conversational memory**: Application state persists independently of agent conversations. In production, this would be stored in SQLite or PostgreSQL.

## Phase 12: Evaluation

### What it does
A real evaluation pipeline (not fake) measuring:
- **Recall@K**: % of expected keywords found in the RAG answer
- **Source Hit Rate**: whether the expected document source was cited
- **Latency**: end-to-end response time

Run with `pytest tests/test_evaluation.py`.

## Phase 13: Guardrails

### What it does
Input validation layer applied before any LLM call:
- Prompt injection pattern detection (regex-based)
- PII redaction (SSN, credit card, phone)
- Length validation

### Limitations (documented)
- Regex-based injection detection is not foolproof. Adversarial prompts can evade it.
- Not a complete security solution — defense in depth is required in production.
- PII detection only covers common patterns; specialized NER models would be more accurate.

## Phase 14: Productionization

### What it does
Dockerfile (Python 3.11-slim), docker-compose (API + Qdrant with persistent volume), GitHub Actions CI (runs pytest on every push), and complete README.

### Key Decisions
- **Qdrant persistence**: docker-compose uses a named volume `qdrant_data` so vectors survive container restarts.
- **Layer caching**: `pyproject.toml` is copied before app code so the `pip install` layer is cached unless dependencies change.

## Storage foundation: PostgreSQL preferences and Redis sessions

### What this component does
Candidate search preferences are validated as a Pydantic model and upserted in
PostgreSQL through a SQLAlchemy repository. Recent conversation messages are
stored separately in Redis, trimmed to a configurable maximum, and assigned a
TTL. Alembic owns the PostgreSQL schema lifecycle.

### Why it exists
Preferences must survive API restarts and be available across conversations.
Conversation messages are short-lived context, so Redis is a better fit than
mixing them into durable profile data. Keeping the stores separate makes their
retention and failure behavior explicit.

### Important design decisions
- SQLAlchemy 2.x provides a typed repository boundary; Alembic applies explicit
	migrations instead of creating production tables as an import/startup side
	effect.
- The PostgreSQL row stores the validated preference object as JSON so the
	search profile can evolve without one migration for every optional filter.
- Redis stores role/content messages in a list, trims old entries atomically,
	and refreshes the configured expiration when a message is appended.
- Store instances are injectable. Tests use SQLite for repository behavior and
	fakeredis for the Redis command contract, so the unit suite needs no running
	services.

### Alternatives considered
- SQLite is useful for local unit tests, but PostgreSQL is the configured
	durable store because it is the requested production database and supports
	the later pgvector search phase.
- An in-process dictionary is simpler, but loses preferences on restart and
	cannot share state across API workers.
- PostgreSQL JSON is selected for the first preference schema. A later
	relational job index can add typed columns for hard filters without forcing
	the preference shape to be fully normalized.

### Limitations
- Candidate and session identifiers are caller-supplied. Authentication,
	authorization, and ownership checks are not implemented; do not expose these
	endpoints to untrusted users yet.
- Conversation messages are stored as plain text. No transcript encryption,
	PII redaction, or user deletion workflow is provided by this slice.
- The pgvector-enabled PostgreSQL image is configured, but no vector columns or
	hybrid retrieval are implemented yet.
- PostgreSQL/Redis service health is not part of the API health endpoint; the
	configured flags only indicate that clients/repositories were constructed.
