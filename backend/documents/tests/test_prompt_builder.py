from types import SimpleNamespace

from django.test import SimpleTestCase

from documents.services.prompt_builder import PromptBuilder


class PromptBuilderTests(SimpleTestCase):

    def setUp(self):
        document = SimpleNamespace(title="Scientific Paper")

        page = SimpleNamespace(
            document=document,
            page_number=12,
        )

        self.chunk = SimpleNamespace(
            page=page,
            text="RDF represents information using subject-predicate-object triples.",
        )

    def test_build_includes_question(self):
        prompt = PromptBuilder.build(
            "What is RDF?",
            [self.chunk],
        )

        self.assertIn("What is RDF?", prompt)

    def test_build_includes_source_text(self):
        prompt = PromptBuilder.build(
            "What is RDF?",
            [self.chunk],
        )

        self.assertIn(
            "RDF represents information using subject-predicate-object triples.",
            prompt,
        )

    def test_build_includes_document_and_page(self):
        prompt = PromptBuilder.build(
            "What is RDF?",
            [self.chunk],
        )

        self.assertIn("Scientific Paper", prompt)
        self.assertIn("Page: 12", prompt)

    def test_build_includes_citation_instructions(self):
        prompt = PromptBuilder.build(
            "What is RDF?",
            [self.chunk],
        )

        self.assertIn("Cite supporting passages", prompt)
        self.assertIn("[Source 1]", prompt)

    def test_build_rejects_empty_question(self):
        with self.assertRaises(ValueError):
            PromptBuilder.build("   ", [self.chunk])

    def test_build_rejects_empty_chunks(self):
        with self.assertRaises(ValueError):
            PromptBuilder.build("What is RDF?", [])

    def test_build_numbers_multiple_sources(self):
        prompt = PromptBuilder.build(
            "What is RDF?",
            [self.chunk, self.chunk],
        )

        self.assertIn("[Source 1 |", prompt)
        self.assertIn("[Source 2 |", prompt)

    def test_build_instructs_model_to_avoid_unsupported_answers(self):
        prompt = PromptBuilder.build(
            "What is RDF?",
            [self.chunk],
        )

        self.assertIn("Do not use outside knowledge", prompt)
        self.assertIn("cannot be determined", prompt)