
"""Tests for the retrieval evaluation runner."""

from types import SimpleNamespace
from unittest.mock import Mock

from django.test import SimpleTestCase

from documents.evaluation.runner import RetrievalEvaluationRunner


class RetrievalEvaluationRunnerTests(SimpleTestCase):

    def test_evaluate_all_strategies(self):
        chunks = [
            SimpleNamespace(id=10),
            SimpleNamespace(id=20),
            SimpleNamespace(id=30),
        ]

        retrieval_service = Mock()
        retrieval_service.search.return_value = chunks

        reranking_service = Mock()
        reranking_service.rerank.return_value = [
            chunks[1],
            chunks[0],
            chunks[2],
        ]

        runner = RetrievalEvaluationRunner(
            retrieval_service=retrieval_service,
            reranking_service=reranking_service,
        )

        dataset = {
            "cases": [
                {
                    "id": "example",
                    "question": "Example question?",
                    "document_id": 5,
                    "relevant_chunk_ids": [20],
                }
            ]
        }

        results = runner.evaluate(dataset, limit=10)

        self.assertEqual(
            results["semantic"]["recall_at_1"],
            0.0,
        )

        self.assertEqual(
            results["hybrid"]["recall_at_5"],
            1.0,
        )

        self.assertEqual(
            results["hybrid_reranked"]["recall_at_1"],
            1.0,
        )

        self.assertEqual(
            results["hybrid_reranked"]["mrr"],
            1.0,
        )

        self.assertEqual(
            retrieval_service.search.call_count,
            3,
        )

    def test_rejects_invalid_strategy(self):
        runner = RetrievalEvaluationRunner(
            retrieval_service=Mock(),
        )

        with self.assertRaises(ValueError):
            runner.retrieve(
                "Question?",
                document_id=5,
                strategy="invalid",
            )

    def test_rejects_empty_dataset(self):
        runner = RetrievalEvaluationRunner(
            retrieval_service=Mock(),
        )

        with self.assertRaises(ValueError):
            runner.evaluate({"cases": []})
