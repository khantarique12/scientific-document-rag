
"""Evaluate retrieval strategies against labeled document chunks."""

import json
from pathlib import Path

from documents.evaluation.metrics import (
    mean_reciprocal_rank,
    recall_at_k,
)
from documents.services.retrieval import RetrievalService
from documents.services.reranking import RerankingService


class RetrievalEvaluationRunner:
    """Compare semantic, hybrid, and reranked retrieval."""

    STRATEGIES = (
        "semantic",
        "hybrid",
        "hybrid_reranked",
    )

    def __init__(
        self,
        retrieval_service=None,
        reranking_service=None,
    ):
        self.retrieval_service = (
            retrieval_service
            if retrieval_service is not None
            else RetrievalService()
        )
        self.reranking_service = reranking_service

    @staticmethod
    def load_dataset(path):
        with Path(path).open(encoding="utf-8") as file:
            return json.load(file)

    def retrieve(self, question, document_id, strategy, limit=10):
        if strategy not in self.STRATEGIES:
            raise ValueError("Unsupported evaluation strategy.")

        if limit <= 0:
            raise ValueError("Limit must be positive.")

        retrieval_strategy = (
            "semantic"
            if strategy == "semantic"
            else "hybrid"
        )

        candidate_limit = (
            max(limit, 30)
            if strategy == "hybrid_reranked"
            else limit
        )

        chunks = self.retrieval_service.search(
            question,
            limit=candidate_limit,
            document_id=document_id,
            strategy=retrieval_strategy,
        )

        if strategy == "hybrid_reranked":
            if self.reranking_service is None:
                self.reranking_service = RerankingService()

            chunks = self.reranking_service.rerank(
                question,
                chunks,
                limit=limit,
            )

        return [chunk.id for chunk in chunks[:limit]]

    def evaluate(self, dataset, limit=10):
        if limit <= 0:
            raise ValueError("Limit must be positive.")

        cases = dataset["cases"]

        if not cases:
            raise ValueError("Evaluation dataset cannot be empty.")

        results = {}

        for strategy in self.STRATEGIES:
            rankings = []
            relevant_sets = []
            case_results = []

            for case in cases:
                retrieved_ids = self.retrieve(
                    question=case["question"],
                    document_id=case["document_id"],
                    strategy=strategy,
                    limit=limit,
                )

                relevant_ids = set(case["relevant_chunk_ids"])

                rankings.append(retrieved_ids)
                relevant_sets.append(relevant_ids)

                case_results.append({
                    "id": case["id"],
                    "retrieved_chunk_ids": retrieved_ids,
                    "relevant_chunk_ids": sorted(relevant_ids),
                    "recall_at_1": recall_at_k(
                        retrieved_ids, relevant_ids, 1
                    ),
                    "recall_at_5": recall_at_k(
                        retrieved_ids, relevant_ids, 5
                    ),
                    "recall_at_10": recall_at_k(
                        retrieved_ids, relevant_ids, 10
                    ),
                })

            results[strategy] = {
                "recall_at_1": sum(
                    case["recall_at_1"] for case in case_results
                ) / len(case_results),
                "recall_at_5": sum(
                    case["recall_at_5"] for case in case_results
                ) / len(case_results),
                "recall_at_10": sum(
                    case["recall_at_10"] for case in case_results
                ) / len(case_results),
                "mrr": mean_reciprocal_rank(
                    rankings,
                    relevant_sets,
                ),
                "cases": case_results,
            }

        return results
