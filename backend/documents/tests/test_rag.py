
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

        self.reranker = Mock()
        self.reranker.rerank.return_value = [self.chunk]

        self.llm = Mock()
        self.llm.generate.return_value = (
            "RDF represents data using triples [Source 1]."
        )

        self.builder = Mock()
        self.builder.build.return_value = "Generated prompt"

        self.service = RAGService(
            retrieval_service=self.retrieval,
            reranking_service=self.reranker,
            llm_client=self.llm,
            prompt_builder=self.builder,
            use_context_selection=False,
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
            limit=30,
            document_id=None,
        )

    def test_ask_filters_by_document(self):
        self.service.ask(
            "What is RDF?",
            limit=3,
            document_id=1,
        )

        self.retrieval.search.assert_called_once_with(
            "What is RDF?",
            limit=30,
            document_id=1,
        )

    def test_ask_calls_reranker(self):
        self.service.ask("What is RDF?", limit=3)

        self.reranker.rerank.assert_called_once_with(
            "What is RDF?",
            [self.chunk],
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
        self.assertEqual(
            source["text"],
            "RDF represents data using triples.",
        )

    def test_ask_handles_no_retrieved_chunks(self):
        self.retrieval.search.return_value = []

        result = self.service.ask("Unknown question")

        self.assertEqual(result["sources"], [])
        self.assertIn(
            "cannot be determined",
            result["answer"],
        )

        self.reranker.rerank.assert_not_called()
        self.llm.generate.assert_not_called()

    def test_ask_rejects_empty_question(self):
        with self.assertRaises(ValueError):
            self.service.ask("   ")

        self.retrieval.search.assert_not_called()
        self.reranker.rerank.assert_not_called()

    def test_ask_rejects_invalid_limit(self):
        with self.assertRaises(ValueError):
            self.service.ask("What is RDF?", limit=0)

        self.retrieval.search.assert_not_called()
        self.reranker.rerank.assert_not_called()

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

    def test_ask_uses_reranked_chunks(self):
        another_page = SimpleNamespace(
            document=self.chunk.page.document,
            page_number=23,
        )

        better_chunk = SimpleNamespace(
            id=20,
            page=another_page,
            text="SMART criteria are Specific, Measurable, "
                 "Achievable, Relevant, and Time-bound.",
            distance=0.3,
        )

        self.retrieval.search.return_value = [
            self.chunk,
            better_chunk,
        ]

        self.reranker.rerank.return_value = [better_chunk]

        result = self.service.ask(
            "What are the SMART criteria?",
            limit=1,
        )

        self.assertEqual(result["sources"][0]["chunk_id"], 20)
        self.assertEqual(result["sources"][0]["page_number"], 23)

        self.builder.build.assert_called_once_with(
            "What are the SMART criteria?",
            [better_chunk],
        )

    def test_ask_without_reranking(self):
        service = RAGService(
            retrieval_service=self.retrieval,
            reranking_service=self.reranker,
            llm_client=self.llm,
            prompt_builder=self.builder,
            use_reranking=False,
            use_context_selection=False,
        )

        service.ask("What is RDF?", limit=3)

        self.retrieval.search.assert_called_once_with(
            "What is RDF?",
            limit=3,
            document_id=None,
        )

        self.reranker.rerank.assert_not_called()

    
    def test_ask_applies_context_selection(self):
        selector = Mock()
        selector.select.return_value = [self.chunk]

        service = RAGService(
            retrieval_service=self.retrieval,
            reranking_service=self.reranker,
            context_selection_service=selector,
            llm_client=self.llm,
            prompt_builder=self.builder,
            use_context_selection=True,
        )

        result = service.ask("What is RDF?", limit=5)

        self.reranker.rerank.assert_called_once_with(
            "What is RDF?",
            [self.chunk],
            limit=10,
        )

        selector.select.assert_called_once_with(
            [self.chunk],
            limit=5,
        )

        self.assertEqual(result["sources"][0]["chunk_id"], 10)

