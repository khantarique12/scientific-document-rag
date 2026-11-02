
"""Evaluate document-grounded RAG answers."""

import json
import time
from pathlib import Path

from documents.services.rag import RAGService


class AnswerEvaluationRunner:
    """Run RAG questions and record answer evaluation data."""

    def __init__(self, rag_service=None):
        self.rag_service = (
            rag_service
            if rag_service is not None
            else RAGService()
        )

    @staticmethod
    def load_dataset(path):
        """Load evaluation questions from JSON."""
        with Path(path).open(encoding="utf-8") as file:
            return json.load(file)

    def evaluate(self, dataset, limit=5, verify_citations=False):
        """Evaluate answers using the existing RAG pipeline."""

        if limit <= 0:
            raise ValueError("Limit must be positive.")

        cases = dataset.get("cases", [])

        if not cases:
            raise ValueError("Evaluation dataset cannot be empty.")

        results = []

        for case in cases:
            start = time.perf_counter()

            response = self.rag_service.ask(
                question=case["question"],
                document_id=case["document_id"],
                limit=limit,
                verify_citations=verify_citations,
            )

            elapsed = time.perf_counter() - start

            answer = response["answer"]

            expected_facts = case.get("expected_facts", [])

            matched_facts = [
                fact
                for fact in expected_facts
                if fact.casefold() in answer.casefold()
            ]

            fact_coverage = (
                len(matched_facts) / len(expected_facts)
                if expected_facts
                else None
            )

            results.append({
                "id": case["id"],
                "question": case["question"],
                "answer": answer,
                "expected_facts": expected_facts,
                "matched_facts": matched_facts,
                "fact_coverage": fact_coverage,
                "sources": response.get("sources", []),
                "citations": response.get("citations", []),
                "invalid_citations": response.get(
                    "invalid_citations", []
                ),
                "citation_verification": response.get(
                    "citation_verification", []
                ),
                "response_time_seconds": round(elapsed, 3),
            })

        return {
            "total_cases": len(results),
            "average_fact_coverage": (
                sum(
                    result["fact_coverage"]
                    for result in results
                    if result["fact_coverage"] is not None
                )
                / sum(
                    result["fact_coverage"] is not None
                    for result in results
                )
                if any(
                    result["fact_coverage"] is not None
                    for result in results
                )
                else None
            ),
            "average_response_time_seconds": round(
                sum(
                    result["response_time_seconds"]
                    for result in results
                ) / len(results),
                3,
            ),
            "cases": results,
        }
