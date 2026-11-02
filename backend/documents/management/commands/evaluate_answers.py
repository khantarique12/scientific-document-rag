
"""Run the RAG answer-quality evaluation benchmark."""

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from documents.evaluation.answer_runner import AnswerEvaluationRunner


class Command(BaseCommand):
    help = "Evaluate RAG answers against a labeled question dataset."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dataset",
            required=True,
            help="Path to the answer-evaluation JSON dataset.",
        )
        parser.add_argument(
            "--output",
            required=True,
            help="Path where the evaluation report will be saved.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=5,
            help="Maximum number of evidence chunks per question.",
        )
        parser.add_argument(
            "--verify-citations",
            action="store_true",
            help="Enable claim-level citation verification.",
        )

    def handle(self, *args, **options):
        dataset_path = Path(options["dataset"])
        output_path = Path(options["output"])

        if not dataset_path.is_file():
            raise CommandError(
                f"Dataset not found: {dataset_path}"
            )

        if options["limit"] <= 0:
            raise CommandError("--limit must be positive.")


        try:
            dataset = AnswerEvaluationRunner.load_dataset(dataset_path)

            if not isinstance(dataset, dict):
                raise ValueError("Dataset must be a JSON object.")

            cases = dataset.get("cases")

            if not isinstance(cases, list) or not cases:
                raise ValueError(
                    "Dataset must contain a non-empty cases list."
                )

            for index, case in enumerate(cases, start=1):
                if not isinstance(case, dict):
                    raise ValueError(
                        f"Case {index} must be a JSON object."
                    )

                for field in ("id", "question", "document_id"):
                    if field not in case:
                        raise ValueError(
                            f"Case {index} is missing '{field}'."
                        )

                if not isinstance(case["question"], str) or not case["question"].strip():
                    raise ValueError(
                        f"Case {index} must have a non-empty question."
                    )

                expected_facts = case.get("expected_facts", [])

                if (
                    not isinstance(expected_facts, list)
                    or not all(
                        isinstance(fact, str) and fact.strip()
                        for fact in expected_facts
                    )
                ):
                    raise ValueError(
                        f"Case {index} has invalid expected_facts."
                    )

            runner = AnswerEvaluationRunner()

            report = runner.evaluate(
                dataset,
                limit=options["limit"],
                verify_citations=options["verify_citations"],
            )

        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            raise CommandError(str(exc)) from exc


        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Evaluated {report['total_cases']} questions."
            )
        )

        coverage = report["average_fact_coverage"]

        self.stdout.write(
            "Average expected-term coverage: "
            + (
                f"{coverage:.3f}"
                if coverage is not None
                else "N/A"
            )
        )

        self.stdout.write(
            "Average response time: "
            f"{report['average_response_time_seconds']:.3f}s"
        )

        self.stdout.write(f"Report saved to: {output_path}")
