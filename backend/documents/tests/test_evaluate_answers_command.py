
"""Tests for the evaluate_answers management command."""

import json
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase


class EvaluateAnswersCommandTests(SimpleTestCase):
    """Test the management command without running the RAG pipeline."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.directory = Path(self.temp_dir.name)
        self.dataset_path = self.directory / "dataset.json"
        self.output_path = self.directory / "results" / "report.json"

        self.dataset = {
            "cases": [
                {
                    "id": "test_question",
                    "question": "What is RMSE?",
                    "document_id": 1,
                    "expected_facts": ["RMSE"],
                }
            ]
        }

        self.dataset_path.write_text(
            json.dumps(self.dataset),
            encoding="utf-8",
        )

    @patch(
        "documents.management.commands.evaluate_answers."
        "AnswerEvaluationRunner.evaluate"
    )
    def test_command_writes_report(self, mock_evaluate):
        """The command should save the evaluation report."""

        mock_evaluate.return_value = {
            "total_cases": 1,
            "average_fact_coverage": 1.0,
            "average_response_time_seconds": 0.5,
            "cases": [
                {
                    "id": "test_question",
                    "answer": "RMSE is root mean squared error.",
                    "fact_coverage": 1.0,
                }
            ],
        }

        output = StringIO()

        call_command(
            "evaluate_answers",
            dataset=str(self.dataset_path),
            output=str(self.output_path),
            stdout=output,
        )

        self.assertTrue(self.output_path.is_file())

        saved = json.loads(
            self.output_path.read_text(encoding="utf-8")
        )

        self.assertEqual(saved["total_cases"], 1)
        self.assertEqual(saved["average_fact_coverage"], 1.0)

        mock_evaluate.assert_called_once_with(
            self.dataset,
            limit=5,
            verify_citations=False,
        )

        self.assertIn(
            "Evaluated 1 questions",
            output.getvalue(),
        )

    def test_command_rejects_missing_dataset(self):
        """A missing dataset must produce a command error."""

        with self.assertRaises(CommandError):
            call_command(
                "evaluate_answers",
                dataset=str(self.directory / "missing.json"),
                output=str(self.output_path),
            )

        self.assertFalse(self.output_path.exists())

    def test_command_rejects_invalid_limit(self):
        """The command must reject nonpositive retrieval limits."""

        with self.assertRaises(CommandError):
            call_command(
                "evaluate_answers",
                dataset=str(self.dataset_path),
                output=str(self.output_path),
                limit=0,
            )

        self.assertFalse(self.output_path.exists())

    @patch(
        "documents.management.commands.evaluate_answers."
        "AnswerEvaluationRunner.evaluate"
    )
    def test_command_passes_verification_option(self, mock_evaluate):
        """Citation verification should be forwarded to the runner."""

        mock_evaluate.return_value = {
            "total_cases": 1,
            "average_fact_coverage": None,
            "average_response_time_seconds": 0.5,
            "cases": [],
        }

        call_command(
            "evaluate_answers",
            dataset=str(self.dataset_path),
            output=str(self.output_path),
            verify_citations=True,
            stdout=StringIO(),
        )

        mock_evaluate.assert_called_once_with(
            self.dataset,
            limit=5,
            verify_citations=True,
        )

    def test_command_rejects_invalid_json(self):
        """Malformed JSON must produce a command error."""

        self.dataset_path.write_text(
            "{invalid json",
            encoding="utf-8",
        )

        with self.assertRaises(CommandError):
            call_command(
                "evaluate_answers",
                dataset=str(self.dataset_path),
                output=str(self.output_path),
            )

        self.assertFalse(self.output_path.exists())

    def test_command_rejects_empty_dataset(self):
        """A dataset without cases must be rejected."""

        self.dataset_path.write_text(
            json.dumps({"cases": []}),
            encoding="utf-8",
        )

        with self.assertRaisesMessage(
            CommandError,
            "Dataset must contain a non-empty cases list.",
        ):
            call_command(
                "evaluate_answers",
                dataset=str(self.dataset_path),
                output=str(self.output_path),
            )

    def test_command_rejects_missing_question(self):
        """Each case must contain a question."""

        invalid_dataset = {
            "cases": [
                {
                    "id": "missing_question",
                    "document_id": 1,
                    "expected_facts": ["RMSE"],
                }
            ]
        }

        self.dataset_path.write_text(
            json.dumps(invalid_dataset),
            encoding="utf-8",
        )

        with self.assertRaisesMessage(
            CommandError,
            "Case 1 is missing 'question'.",
        ):
            call_command(
                "evaluate_answers",
                dataset=str(self.dataset_path),
                output=str(self.output_path),
            )
