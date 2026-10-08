from unittest.mock import Mock

from django.test import TestCase

from documents.models import Chunk, Document, Page
from documents.services.indexing import IndexingService


class IndexingServiceTests(TestCase):
    def setUp(self):
        self.document = Document.objects.create(
            title="Scientific Paper",
            original_filename="paper.pdf",
            file="documents/paper.pdf",
        )

        self.page = Page.objects.create(
            document=self.document,
            page_number=1,
            text="Scientific page text.",
        )

        self.chunk = Chunk.objects.create(
            page=self.page,
            chunk_index=0,
            text="Semantic technologies support interoperability.",
        )

    def test_index_chunk_generates_and_saves_embedding(self):
        embedding = [0.1] * 384

        embedding_service = Mock()
        embedding_service.embed.return_value = embedding

        service = IndexingService(
            embedding_service=embedding_service,
        )

        result = service.index_chunk(self.chunk)

        self.chunk.refresh_from_db()

        self.assertIsNotNone(self.chunk.embedding)
        self.assertEqual(len(self.chunk.embedding), 384)
        self.assertEqual(result.id, self.chunk.id)

        embedding_service.embed.assert_called_once_with(
            self.chunk.text
        )

    def test_index_chunks_generates_and_saves_embeddings(self):
        second_chunk = Chunk.objects.create(
            page=self.page,
            chunk_index=1,
            text="Knowledge graphs support data integration.",
        )

        first_embedding = [0.1] * 384
        second_embedding = [0.2] * 384

        embedding_service = Mock()
        embedding_service.embed_batch.return_value = [
            first_embedding,
            second_embedding,
        ]

        service = IndexingService(
            embedding_service=embedding_service,
        )

        chunks = [self.chunk, second_chunk]
        result = service.index_chunks(chunks)

        self.chunk.refresh_from_db()
        second_chunk.refresh_from_db()

        self.assertEqual(len(result), 2)
        self.assertEqual(len(self.chunk.embedding), 384)
        self.assertEqual(len(second_chunk.embedding), 384)

        embedding_service.embed_batch.assert_called_once_with(
            [
                self.chunk.text,
                second_chunk.text,
            ]
        )

    def test_index_chunks_with_empty_list_returns_empty_list(self):
        embedding_service = Mock()

        service = IndexingService(
            embedding_service=embedding_service,
        )

        result = service.index_chunks([])

        self.assertEqual(result, [])
        embedding_service.embed_batch.assert_not_called()

    def test_index_chunks_rejects_embedding_count_mismatch(self):
        second_chunk = Chunk.objects.create(
            page=self.page,
            chunk_index=1,
            text="Second chunk.",
        )

        embedding_service = Mock()
        embedding_service.embed_batch.return_value = [
            [0.1] * 384,
        ]

        service = IndexingService(
            embedding_service=embedding_service,
        )

        with self.assertRaises(ValueError):
            service.index_chunks(
                [self.chunk, second_chunk]
            )

        self.chunk.refresh_from_db()
        second_chunk.refresh_from_db()

        self.assertIsNone(self.chunk.embedding)
        self.assertIsNone(second_chunk.embedding)

    def test_index_chunks_processes_multiple_batches(self):
        second_chunk = Chunk.objects.create(
            page=self.page,
            chunk_index=1,
            text="Second chunk.",
        )
        third_chunk = Chunk.objects.create(
            page=self.page,
            chunk_index=2,
            text="Third chunk.",
        )

        embedding_service = Mock()
        embedding_service.embed_batch.side_effect = [
            [
                [0.1] * 384,
                [0.2] * 384,
            ],
            [
                [0.3] * 384,
            ],
        ]

        service = IndexingService(
            embedding_service=embedding_service,
        )

        service.index_chunks(
            [self.chunk, second_chunk, third_chunk],
            batch_size=2,
        )

        self.assertEqual(
            embedding_service.embed_batch.call_count,
            2,
        )

        self.chunk.refresh_from_db()
        second_chunk.refresh_from_db()
        third_chunk.refresh_from_db()

        self.assertIsNotNone(self.chunk.embedding)
        self.assertIsNotNone(second_chunk.embedding)
        self.assertIsNotNone(third_chunk.embedding)

    def test_index_chunks_rejects_invalid_batch_size(self):
        embedding_service = Mock()

        service = IndexingService(
            embedding_service=embedding_service,
        )

        with self.assertRaises(ValueError):
            service.index_chunks(
                [self.chunk],
                batch_size=0,
            )

        embedding_service.embed_batch.assert_not_called()