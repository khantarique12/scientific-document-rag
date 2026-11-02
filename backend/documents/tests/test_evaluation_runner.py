
"""Tests for the retrieval evaluation runner."""

from types import SimpleNamespace
from unittest.mock import Mock

from django.test import SimpleTestCase

from documents.evaluation.runner import RetrievalEvaluationRunner


class RetrievalEvaluationRunnerTests(SimpleTestCase):
    """Test retrieval strategy evaluation without database access."""

    def setUp(self):
        self.retrieval_service = Mock()
        self.reranking_service = Mock()

        self.runner = RetrievalEvaluationRunner(
            retrieval_service=self.retrieval_service,
            reranking_service=self.reranking_service,
        )

        self.dataset = {
            "cases": [
                {
                    "id": "question_1",
                    "question": "What is a KPI?",
                    "document_id": 1,
                    "relevant_chunk_ids": [2, 3],
                },
                {
                    "id": "question_2",
                    "question": "How are KPIs validated?",
                    "document_id": 1,
                    "relevant_chunk_ids": [5],
                },
            ]
        }

    def test_evaluate_all_strategies(self):
        """All strategies should return correct retrieval metrics."""

        chunks = [
            SimpleNamespace(id=1),
            SimpleNamespace(id=2),
            SimpleNamespace(id=3),
            SimpleNamespace(id=4),
            SimpleNamespace(id=5),
        ]

        self.retrieval_service.search.return_value = chunks
        self.reranking_service.rerank.return_value = [
            chunks[1],
            chunks[2],
            chunks[4],
            chunks[0],
            chunks[3],
        ]

        results = self.runner.evaluate(self.dataset, limit=5)

        self.assertEqual(
            set(results),
            set(self.runner.STRATEGIES),
        )

        for strategy in self.runner.STRATEGIES:
            result = results[strategy]

            self.assertEqual(len(result["cases"]), 2)

            for metric in (
                "recall_at_1",
                "recall_at_5",
                "recall_at_10",
                "hit_at_1",
                "hit_at_5",
                "hit_at_10",
                "mrr",
            ):
                self.assertIn(metric, result)
                self.assertGreaterEqual(result[metric], 0.0)
                self.assertLessEqual(result[metric], 1.0)

            for case in result["cases"]:
                relevant = set(case["relevant_chunk_ids"])
                retrieved = case["retrieved_chunk_ids"]

                for k in (1, 5, 10):
                    expected_hit = float(
                        bool(set(retrieved[:k]) & relevant)
                    )

                    self.assertEqual(
                        case[f"hit_at_{k}"],
                        expected_hit,
                    )

                    expected_recall = (
                        len(set(retrieved[:k]) & relevant)
                        / len(relevant)
                    )

                    self.assertAlmostEqual(
                        case[f"recall_at_{k}"],
                        expected_recall,
                    )

            for k in (1, 5, 10):
                expected_hit = sum(
                    case[f"hit_at_{k}"]
                    for case in result["cases"]
                ) / len(result["cases"])

                self.assertAlmostEqual(
                    result[f"hit_at_{k}"],
                    expected_hit,
                )

        # Check known results for the semantic strategy.
        semantic = results["semantic"]

        self.assertAlmostEqual(semantic["hit_at_1"], 0.0)
        self.assertAlmostEqual(semantic["hit_at_5"], 1.0)
        self.assertAlmostEqual(semantic["hit_at_10"], 1.0)
        self.assertAlmostEqual(semantic["recall_at_5"], 1.0)
        self.assertAlmostEqual(semantic["mrr"], 0.35)

        # The reranked strategy puts relevant chunks first.
        reranked = results["hybrid_reranked"]

        self.assertAlmostEqual(reranked["hit_at_1"], 0.5)
        self.assertAlmostEqual(reranked["hit_at_5"], 1.0)
        self.assertAlmostEqual(reranked["mrr"], 2 / 3)

        self.assertEqual(
            self.reranking_service.rerank.call_count,
            len(self.dataset["cases"]),
        )

    def test_rejects_empty_dataset(self):
        """An empty evaluation dataset must be rejected."""

        with self.assertRaises(ValueError):
            self.runner.evaluate({"cases": []})

    def test_rejects_invalid_strategy(self):
        """Unknown retrieval strategies must be rejected."""

        with self.assertRaises(ValueError):
            self.runner.retrieve(
                question="Test question",
                document_id=1,
                strategy="invalid",
            )
