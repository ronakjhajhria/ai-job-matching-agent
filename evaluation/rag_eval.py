"""Phase 12: Evaluation pipeline for RAG and Agent quality."""

import json
import logging
import time
from pathlib import Path
from pydantic import BaseModel

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Evaluation Dataset Schema
# --------------------------------------------------------------------------- #
class EvalSample(BaseModel):
    question: str
    expected_keywords: list[str]  # Keywords we expect in the answer
    expected_sources: list[str]   # Document sources we expect to be cited


class EvalResult(BaseModel):
    question: str
    answer: str
    cited_sources: list[str]
    keywords_found: list[str]
    keywords_missing: list[str]
    recall_at_k: float   # % of expected keywords found
    source_hit: bool     # Was at least one expected source cited?
    latency_ms: float


class EvalReport(BaseModel):
    total_samples: int
    avg_recall_at_k: float
    source_hit_rate: float
    avg_latency_ms: float
    results: list[EvalResult]


# --------------------------------------------------------------------------- #
# Built-in Evaluation Dataset
# --------------------------------------------------------------------------- #
BUILTIN_EVAL_SAMPLES = [
    EvalSample(
        question="What programming languages does the candidate know?",
        expected_keywords=["python"],
        expected_sources=["resume"]
    ),
    EvalSample(
        question="What are the job responsibilities?",
        expected_keywords=["microservices", "deploy"],
        expected_sources=["job"]
    ),
]


# --------------------------------------------------------------------------- #
# Evaluator
# --------------------------------------------------------------------------- #
class RAGEvaluator:
    """
    Evaluates RAG quality using Recall@K and Source Hit Rate.
    
    Metrics:
    - Recall@K: % of expected keywords found in the answer (using K=top_k retrieved chunks)
    - Source Hit Rate: % of samples where at least one expected source was cited
    - Latency: end-to-end response time in milliseconds
    """
    
    def __init__(self, rag_generator, top_k: int = 5):
        self.generator = rag_generator
        self.top_k = top_k

    def evaluate_sample(self, sample: EvalSample) -> EvalResult:
        start = time.monotonic()
        
        try:
            response = self.generator.answer_question(sample.question, top_k=self.top_k)
            answer = response.answer
            cited_sources = [c.source_document for c in response.citations]
        except Exception as e:
            logger.error(f"Evaluation error: {e}")
            answer = ""
            cited_sources = []

        latency_ms = (time.monotonic() - start) * 1000
        answer_lower = answer.lower()

        keywords_found = [kw for kw in sample.expected_keywords if kw.lower() in answer_lower]
        keywords_missing = [kw for kw in sample.expected_keywords if kw.lower() not in answer_lower]
        recall = len(keywords_found) / len(sample.expected_keywords) if sample.expected_keywords else 1.0
        source_hit = any(src.lower() in " ".join(cited_sources).lower() for src in sample.expected_sources)

        return EvalResult(
            question=sample.question,
            answer=answer,
            cited_sources=cited_sources,
            keywords_found=keywords_found,
            keywords_missing=keywords_missing,
            recall_at_k=recall,
            source_hit=source_hit,
            latency_ms=round(latency_ms, 2)
        )

    def evaluate(self, samples: list[EvalSample] | None = None) -> EvalReport:
        samples = samples or BUILTIN_EVAL_SAMPLES
        results = [self.evaluate_sample(s) for s in samples]
        
        avg_recall = sum(r.recall_at_k for r in results) / len(results)
        source_hit_rate = sum(1 for r in results if r.source_hit) / len(results)
        avg_latency = sum(r.latency_ms for r in results) / len(results)

        return EvalReport(
            total_samples=len(results),
            avg_recall_at_k=round(avg_recall, 3),
            source_hit_rate=round(source_hit_rate, 3),
            avg_latency_ms=round(avg_latency, 2),
            results=results
        )
