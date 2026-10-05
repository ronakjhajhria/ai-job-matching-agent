# Interview Notes

## Phase 1: Project Foundation

**Q: Why use an application factory pattern (`create_app`) instead of a global app instance?**
A: It makes application construction explicit and testable. We can inject different settings (like database URLs or mock providers) for unit tests, avoiding coupling test cases to one global configuration instance.

**Q: Why do you validate environment settings using Pydantic?**
A: Configuration errors (like a missing API key or a typo in a log level) should fail fast and early at application startup with a clear validation error. Typed settings also provide a single source of truth for defaults and environment variable names.

**Q: What does your health endpoint actually prove?**
A: It proves the API process is alive and can answer an HTTP request. It does not prove that external dependencies (like an LLM provider or vector DB) are healthy. Those deep health checks will be added when those dependencies are introduced, rather than returning a misleading "all-services-healthy" status now.

## Phase 2: LLM Fundamentals

**Q: Why define an `LLMProvider` protocol instead of calling OpenAI directly?**
A: It follows the Dependency Inversion Principle. The route needs structured generation, not a specific vendor SDK. The protocol keeps that contract explicit, makes the system resilient to vendor lock-in, and allows us to inject a Mock Provider for fast, deterministic unit testing without hitting the network or spending money.

**Q: How do you guarantee the LLM returns the correct JSON format?**
A: We use OpenAI's structured outputs (`beta.chat.completions.parse`) combined with Pydantic. We define the schema as a Pydantic model (`SkillExtraction`), which the SDK converts to a strict JSON schema for the LLM. The SDK then parses and validates the response against that model before returning it to our application, guaranteeing type safety.

**Q: Why not use LangChain right now?**
A: This phase consists of one prompt, one API call, and one Pydantic output schema. The official SDK exposes these cleanly. An orchestration framework like LangChain would add a layer of indirection without solving a workflow problem yet. We prioritize keeping the codebase beginner-friendly and clean, only adding complex tools when the problem demands it (like in the Agent phase).

## Phase 3: Resume/Document Ingestion

**Q: Why do you overlap text chunks when splitting a document?**
A: If we split text without overlap, we risk cutting a sentence or concept perfectly in half. For example, if chunk 1 ends with "I am proficient in" and chunk 2 begins with "Python and Docker", the semantic meaning is lost. Overlapping (e.g., repeating the last 200 characters of the previous chunk) preserves context across boundaries.

**Q: Why use Qdrant instead of just storing vectors in a NumPy array or Postgres?**
A: While a NumPy array works for a small prototype, it requires scanning every single vector (O(N) complexity) to find a match. Qdrant uses Approximate Nearest Neighbor (ANN) algorithms (like HNSW) to perform blazing-fast similarity searches at scale. Also, it natively supports hybrid search (combining vector similarity with metadata filtering). Postgres with `pgvector` is a valid alternative, but Qdrant is purpose-built and easier to spin up standalone.

**Q: What is an Embedding?**
A: An embedding is an array of floating-point numbers that represents the semantic meaning of text. Texts with similar meanings will have embeddings that are geometrically closer to each other in the vector space, which we can measure using metrics like Cosine Similarity.

## Phase 4: Retrieval-Augmented Generation (RAG)

**Q: How do you prevent the LLM from hallucinating in your RAG pipeline?**
A: Two ways. First, via the System Prompt: we explicitly instruct the model to "answer ONLY using the provided context" and "state you do not have enough information if the answer is missing." Second, via Structured Citations: we use Pydantic to force the LLM to return `exact_quote` strings from the context alongside its answer. If it can't quote the context, it can't fulfill the schema.

**Q: What happens if the vector search returns garbage or irrelevant chunks?**
A: The LLM will read the irrelevant chunks, realize the answer to the user's question is not contained within them, and (following its system prompt) reply that it doesn't have enough information. It will not try to guess.

**Q: How do you handle retrieval failures?**
A: If the vector database returns zero chunks (or if we apply a strict similarity threshold and nothing passes), the `RAGAnswerGenerator` immediately returns a hardcoded fallback response. This avoids wasting an API call to the LLM and guarantees a safe failure mode.

## Phases 5 & 6: Intelligence Parsing

**Q: Why use an LLM to parse a resume instead of a library like spaCy?**
A: spaCy requires training data and fails on atypical resume formats. An LLM generalizes across formats by design. The structured output schema (`ResumeProfile`) ensures we always get the fields we need, regardless of how the candidate wrote their resume.

**Q: What if the LLM extracts something that isn't in the resume?**
A: The system prompt explicitly says "extract based ONLY on the provided text." Because we use structured outputs, the model must populate every field — but we trust it to follow the instruction. Future improvement: confidence scores or evidence-anchored extraction.

## Phase 7: Semantic Matching

**Q: Why not use cosine similarity between resume and JD embeddings for matching?**
A: A single embedding of an entire resume loses fine-grained structure. Simple vector similarity would tell us "these texts are somewhat related" without explaining *why* or identifying specific gaps. The LLM approach gives us a named list of matching/missing skills and a human-readable explanation — far more useful for a career intelligence product.

## Phase 8: LangGraph Agent

**Q: What is LangGraph and why use it here?**
A: LangGraph is a library for building stateful multi-step AI agents as explicit state machines. The "graph" part means nodes are functions and edges are routing decisions. Compared to raw ReAct loops, LangGraph prevents infinite loops (bounded iterations), makes state explicit (TypedDict), and keeps tool selection auditable.

**Q: How do you prevent the agent from calling tools randomly?**
A: We use a rule-based router function. It inspects the query for keywords and checks which tools have already been called in `state["tool_calls_made"]`. The agent only calls `job_search` if job-related keywords are in the query AND `job_search` hasn't been called yet. No random tool calls.

**Q: What is your termination condition?**
A: The router returns `"finalize"` when all needed tools have been called or when `iteration_count >= MAX_ITERATIONS` (5). The `finalize` node has an edge to `END`, stopping the graph.

## Phase 12: Evaluation

**Q: How do you evaluate a RAG system?**
A: We use two metrics: Recall@K (what % of expected answer keywords appear in the LLM's response) and Source Hit Rate (did the system cite the correct document). Latency is also tracked. A real production evaluation would also include human feedback scores and faithfulness metrics.

**Q: How do you run the evaluation?**
A: `pytest tests/test_evaluation.py` runs unit tests on the evaluator. For a full end-to-end evaluation against real answers, you'd call `run_evaluation(rag_generator)` after ingesting documents.

## Phase 13: Guardrails

**Q: How do you handle prompt injection attacks?**
A: We run user input through `check_input()` before any LLM call. This uses regex patterns to detect common injection phrases ("ignore all previous instructions", "you are now", etc.). If matched, we return HTTP 400 immediately — the LLM is never called. We also clearly document that this is not a complete defense.

**Q: Why not block PII instead of redacting it?**
A: Blocking would break legitimate resume inputs that happen to contain a phone number. Redaction preserves the semantic content (the user is providing contact info) while preventing that data from being sent to a third-party LLM provider. This is a pragmatic privacy trade-off.

## Storage foundation: PostgreSQL and Redis

**Q: Why store candidate preferences in PostgreSQL and conversation context in Redis?**
A: Preferences are durable user data and need to survive restarts. Conversation
messages are bounded, temporary context with an expiry, so Redis list operations
and TTL fit that lifecycle. Separating them prevents session cleanup from
deleting durable preferences.

**Q: Why use Alembic instead of creating tables when the app imports?**
A: Explicit migrations make schema changes reviewable and deployable in order.
Application imports should not mutate a production database as a side effect.

**Q: Are these endpoints ready for multiple users?**
A: Not yet. IDs are caller-supplied and there is no authentication or ownership
authorization. The storage boundary is implemented, but exposing it safely
requires an identity layer.
