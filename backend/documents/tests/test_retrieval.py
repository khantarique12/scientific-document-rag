from unittest.mock import Mock

from django.test import TestCase

from documents.models import Chunk, Document, Page
from documents.services.retrieval import RetrievalService


class RetrievalServiceTests(TestCase):
    def setUp(self):
        self.document = Document.objects.create(
            title="Scientific Paper",
            original_filename="paper.pdf",
            file="documents/paper.pdf",
        )

        self.page = Page.objects.create(
            document=self.document,
            page_number=1,
            text="Scientific research content.",
        )

        self.first_chunk = Chunk.objects.create(
            page=self.page,
            chunk_index=0,
            text="Research about drought tolerance.",
            embedding=[1.0, 0.0] + [0.0] * 382,
        )

        self.second_chunk = Chunk.objects.create(
            page=self.page,
            chunk_index=1,
            text="Research about data management.",
            embedding=[0.0, 1.0] + [0.0] * 382,
        )

        self.unindexed_chunk = Chunk.objects.create(
            page=self.page,
            chunk_index=2,
            text="Unindexed content.",
        )

        self.embedding_service = Mock()
        self.embedding_service.embed.return_value = (
            [1.0, 0.0] + [0.0] * 382
        )

        self.service = RetrievalService(
            embedding_service=self.embedding_service,
        )

    def test_search_ranks_most_similar_chunk_first(self):
        results = self.service.search("drought tolerance")

        self.assertEqual(results[0].id, self.first_chunk.id)
        self.assertEqual(results[1].id, self.second_chunk.id)

        self.assertLess(
            results[0].distance,
            results[1].distance,
        )

        self.embedding_service.embed.assert_called_once_with(
            "drought tolerance"
        )

    def test_search_excludes_unindexed_chunks(self):
        results = self.service.search("drought tolerance")

        self.assertEqual(len(results), 2)
        self.assertNotIn(self.unindexed_chunk, results)

    def test_search_respects_limit(self):
        results = self.service.search(
            "drought tolerance",
            limit=1,
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, self.first_chunk.id)

    def test_search_rejects_empty_query(self):
        with self.assertRaises(ValueError):
            self.service.search("   ")

        self.embedding_service.embed.assert_not_called()

    def test_search_rejects_invalid_limit(self):
        with self.assertRaises(ValueError):
            self.service.search("drought tolerance", limit=0)

        self.embedding_service.embed.assert_not_called()

    def test_search_includes_source_metadata(self):
        results = self.service.search("drought tolerance")

        first_result = results[0]

        self.assertEqual(first_result.page.page_number, 1)
        self.assertEqual(
            first_result.page.document.title,
            "Scientific Paper",
        )