from types import SimpleNamespace
from unittest.mock import Mock

from django.test import SimpleTestCase

from documents.services.rag import RAGService


class RAGServiceTests(SimpleTestCase):

    def setUp(self):
        document = SimpleNamespace(
            id=1,
            title="Scientific Paper",
        )

        page = SimpleNamespace(
            document=document,
            page_number=12,
        )

        self.chunk = SimpleNamespace(
            id=10,
            page=page,
            text="RDF represents data using triples.",
            distance=0.2,
        )

        self.retrieval = Mock()
        self.retrieval.search.return_value = [self.chunk]

        self.llm = Mock()
        self.llm.generate.return_value = (
            "RDF represents data using triples [Source 1]."
        )

        self.builder = Mock()
        self.builder.build.return_value = "Generated prompt"

        self.service = RAGService(
            retrieval_service=self.retrieval,
            llm_client=self.llm,
            prompt_builder=self.builder,
        )

    def test_ask_returns_generated_answer(self):
        result = self.service.ask("What is RDF?")

        self.assertEqual(
            result["answer"],
            "RDF represents data using triples [Source 1].",
        )

    def test_ask_calls_retrieval(self):
        self.service.ask("What is RDF?", limit=3)

        self.retrieval.search.assert_called_once_with(
            "What is RDF?",
            limit=3,
        )

    def test_ask_builds_prompt(self):
        self.service.ask("What is RDF?")

        self.builder.build.assert_called_once_with(
            "What is RDF?",
            [self.chunk],
        )

        self.llm.generate.assert_called_once_with(
            "Generated prompt"
        )

    def test_ask_returns_source_metadata(self):
        result = self.service.ask("What is RDF?")

        self.assertEqual(len(result["sources"]), 1)

        source = result["sources"][0]

        self.assertEqual(source["document_title"], "Scientific Paper")
        self.assertEqual(source["page_number"], 12)
        self.assertEqual(source["chunk_id"], 10)
        self.assertEqual(source["similarity"], 0.8)

    def test_ask_handles_no_retrieved_chunks(self):
        self.retrieval.search.return_value = []

        result = self.service.ask("Unknown question")

        self.assertEqual(result["sources"], [])
        self.assertIn(
            "cannot be determined",
            result["answer"],
        )

        self.llm.generate.assert_not_called()

    def test_ask_rejects_empty_question(self):
        with self.assertRaises(ValueError):
            self.service.ask("   ")

        self.retrieval.search.assert_not_called()

    def test_ask_rejects_invalid_limit(self):
        with self.assertRaises(ValueError):
            self.service.ask("What is RDF?", limit=0)

        self.retrieval.search.assert_not_called()

    def test_ask_returns_cited_sources(self):
        result = self.service.ask("What is RDF?")

        self.assertEqual(len(result["citations"]), 1)
        self.assertEqual(result["citations"][0]["source_id"], 1)
        self.assertEqual(result["citations"][0]["page_number"], 12)


    def test_ask_returns_empty_citations_without_chunks(self):
        self.retrieval.search.return_value = []

        result = self.service.ask("Unknown question")

        self.assertEqual(result["sources"], [])
        self.assertEqual(result["citations"], [])