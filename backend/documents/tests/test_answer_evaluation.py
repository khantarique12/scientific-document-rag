
"""Tests for RAG answer evaluation."""

from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from documents.evaluation.answer_runner import AnswerEvaluationRunner


class AnswerEvaluationRunnerTests(SimpleTestCase):
    """Test answer evaluation without calling Ollama."""

    def setUp(self):
        self.rag_service = Mock()

        self.runner = AnswerEvaluationRunner(
            rag_service=self.rag_service
        )

        self.dataset = {
            "cases": [
                {
                    "id": "smart_criteria",
                    "question": "What are the SMART criteria?",
                    "document_id": 5,
                    "expected_facts": [
                        "Specific",
                        "Measurable",
                        "Achievable",
                        "Relevant",
                        "Time-bound",
                    ],
                }
            ]
        }

    def test_evaluate_answer_with_all_expected_facts(self):
        """All expected facts should produce full coverage."""

        self.rag_service.ask.return_value = {
            "answer": (
                "SMART means Specific, Measurable, Achievable, "
                "Relevant, and Time-bound."
            ),
            "sources": [{"chunk_id": 102}],
            "citations": [],
        }

        result = self.runner.evaluate(self.dataset)

        self.assertEqual(result["total_cases"], 1)
        self.assertEqual(result["average_fact_coverage"], 1.0)

        case = result["cases"][0]

        self.assertEqual(case["fact_coverage"], 1.0)
        self.assertEqual(len(case["matched_facts"]), 5)
        self.assertEqual(case["sources"][0]["chunk_id"], 102)

        self.rag_service.ask.assert_called_once_with(
            question="What are the SMART criteria?",
            document_id=5,
            limit=5,
            verify_citations=False,
        )

    def test_evaluate_answer_with_partial_facts(self):
        """Missing expected terms should reduce coverage."""

        self.rag_service.ask.return_value = {
            "answer": "Specific and Measurable are SMART criteria.",
            "sources": [],
            "citations": [],
        }

        result = self.runner.evaluate(self.dataset)

        self.assertAlmostEqual(
            result["cases"][0]["fact_coverage"],
            2 / 5,
        )

    def test_evaluate_without_expected_facts(self):
        """Cases without expected facts should remain unscored."""

        dataset = {
            "cases": [
                {
                    "id": "unsupported",
                    "question": "What is the CEO's salary?",
                    "document_id": 5,
                }
            ]
        }

        self.rag_service.ask.return_value = {
            "answer": (
                "The answer cannot be determined from "
                "the provided documents."
            ),
            "sources": [],
            "citations": [],
        }

        result = self.runner.evaluate(dataset)

        self.assertIsNone(
            result["cases"][0]["fact_coverage"]
        )
        self.assertIsNone(
            result["average_fact_coverage"]
        )

    def test_evaluate_with_citation_verification(self):
        """Citation verification results should be retained."""

        self.rag_service.ask.return_value = {
            "answer": "The model uses RMSE [1].",
            "sources": [{"chunk_id": 413}],
            "citations": [{"source_id": 1}],
            "citation_verification": [
                {"claim": "The model uses RMSE", "supported": True}
            ],
        }

        result = self.runner.evaluate(
            self.dataset,
            verify_citations=True,
        )

        case = result["cases"][0]

        self.assertEqual(len(case["citation_verification"]), 1)

        self.rag_service.ask.assert_called_once_with(
            question="What are the SMART criteria?",
            document_id=5,
            limit=5,
            verify_citations=True,
        )


    def test_evaluate_records_invalid_citations(self):
        """Invalid source references must appear in evaluation results."""

        self.rag_service.ask.return_value = {
            "answer": "The LSTM R2 was 0.91 [Source 99].",
            "sources": [{"source_id": 1, "chunk_id": 422}],
            "citations": [],
            "invalid_citations": [99],
        }

        result = self.runner.evaluate(self.dataset)

        self.assertEqual(
            result["cases"][0]["invalid_citations"],
            [99],
        )


    def test_rejects_empty_dataset(self):
        """An empty evaluation dataset must be rejected."""

        with self.assertRaises(ValueError):
            self.runner.evaluate({"cases": []})

    def test_rejects_invalid_limit(self):
        """Retrieval limit must be positive."""

        with self.assertRaises(ValueError):
            self.runner.evaluate(self.dataset, limit=0)

    @patch(
        "documents.evaluation.answer_runner.time.perf_counter",
        side_effect=[10.0, 12.5],
    )
    def test_records_response_time(self, mock_clock):
        """Evaluation should record elapsed time."""

        self.rag_service.ask.return_value = {
            "answer": "Specific",
            "sources": [],
            "citations": [],
        }

        result = self.runner.evaluate(self.dataset)

        self.assertEqual(
            result["cases"][0]["response_time_seconds"],
            2.5,
        )
        self.assertEqual(
            result["average_response_time_seconds"],
            2.5,
        )
