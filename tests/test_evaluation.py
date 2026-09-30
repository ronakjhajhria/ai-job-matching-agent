"""Tests for Phase 12 — Evaluation pipeline."""

import pytest
from evaluation.rag_eval import RAGEvaluator, EvalSample
from app.llm.schemas import RagResponse, Citation


class MockRagGen:
    def answer_question(self, query, top_k=5):
        return RagResponse(
            answer="The candidate knows Python.",
            citations=[Citation(source_document="resume.pdf", exact_quote="Python developer")]
        )


def test_eval_recall_at_k():
    sample = EvalSample(
        question="What languages?",
        expected_keywords=["python", "java"],
        expected_sources=["resume.pdf"]
    )
    evaluator = RAGEvaluator(rag_generator=MockRagGen(), top_k=5)
    result = evaluator.evaluate_sample(sample)

    # "python" is in answer, "java" is not
    assert result.recall_at_k == 0.5
    assert "python" in result.keywords_found
    assert "java" in result.keywords_missing


def test_eval_source_hit():
    sample = EvalSample(
        question="What languages?",
        expected_keywords=["python"],
        expected_sources=["resume.pdf"]
    )
    evaluator = RAGEvaluator(rag_generator=MockRagGen())
    result = evaluator.evaluate_sample(sample)
    assert result.source_hit is True


def test_full_report():
    evaluator = RAGEvaluator(rag_generator=MockRagGen())
    report = evaluator.evaluate([
        EvalSample(question="q1", expected_keywords=["python"], expected_sources=["resume.pdf"]),
        EvalSample(question="q2", expected_keywords=["python", "java"], expected_sources=["resume.pdf"]),
    ])
    assert report.total_samples == 2
    assert 0.0 <= report.avg_recall_at_k <= 1.0
