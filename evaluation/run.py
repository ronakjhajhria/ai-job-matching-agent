"""Entry point for the evaluation suite: python -m evaluation.run"""

import sys
import json
from evaluation.rag_eval import RAGEvaluator, BUILTIN_EVAL_SAMPLES


def run_evaluation(rag_generator) -> None:
    """Run the evaluation suite and print a report to stdout."""
    print("\n" + "="*60)
    print("  JobMind RAG Evaluation Report")
    print("="*60)

    evaluator = RAGEvaluator(rag_generator=rag_generator, top_k=5)
    report = evaluator.evaluate(BUILTIN_EVAL_SAMPLES)

    print(f"\nTotal Samples : {report.total_samples}")
    print(f"Avg Recall@K  : {report.avg_recall_at_k:.1%}")
    print(f"Source Hit Rate: {report.source_hit_rate:.1%}")
    print(f"Avg Latency   : {report.avg_latency_ms:.0f}ms")

    print("\n--- Per-Sample Results ---")
    for r in report.results:
        status = "✓" if r.recall_at_k >= 0.8 else "✗"
        print(f"\n{status} Q: {r.question}")
        print(f"  Recall: {r.recall_at_k:.0%} | Source Hit: {r.source_hit} | Latency: {r.latency_ms:.0f}ms")
        if r.keywords_missing:
            print(f"  Missing keywords: {r.keywords_missing}")
    
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    print("To run the evaluation pipeline with a real RAGAnswerGenerator, import run_evaluation from this module.")
    print("For unit tests, run: pytest tests/test_evaluation.py")
