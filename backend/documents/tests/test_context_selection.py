
from types import SimpleNamespace

from django.test import SimpleTestCase

from documents.services.context_selection import ContextSelectionService


class ContextSelectionServiceTests(SimpleTestCase):

    def setUp(self):
        self.service = ContextSelectionService()

    @staticmethod
    def make_chunk(chunk_id, text, document_id=1):
        document = SimpleNamespace(id=document_id)
        page = SimpleNamespace(document=document)

        return SimpleNamespace(
            id=chunk_id,
            page=page,
            text=text,
        )

    def test_preserves_non_overlapping_chunks(self):
        first = self.make_chunk(
            1,
            "RDF represents data using triples.",
        )
        second = self.make_chunk(
            2,
            "Machine learning supports prediction.",
        )

        result = self.service.select([first, second])

        self.assertEqual(result, [first, second])

    def test_removes_substantial_overlap(self):
        shared = " ".join(f"word{i}" for i in range(25))

        first = self.make_chunk(
            1,
            f"Introduction {shared} conclusion",
        )
        second = self.make_chunk(
            2,
            f"Different beginning {shared} different ending",
        )

        result = self.service.select([first, second])

        self.assertEqual(result, [first])

    def test_preserves_chunks_from_different_documents(self):
        shared = " ".join(f"word{i}" for i in range(25))

        first = self.make_chunk(1, shared, document_id=1)
        second = self.make_chunk(2, shared, document_id=2)

        result = self.service.select([first, second])

        self.assertEqual(result, [first, second])

    def test_respects_limit(self):
        chunks = [
            self.make_chunk(1, "RDF semantic triples"),
            self.make_chunk(2, "Machine learning prediction"),
            self.make_chunk(3, "Scientific research methods"),
        ]

        result = self.service.select(chunks, limit=2)

        self.assertEqual(len(result), 2)
        self.assertEqual(result, chunks[:2])

    def test_rejects_invalid_limit(self):
        with self.assertRaises(ValueError):
            self.service.select([], limit=0)

    def test_handles_empty_chunks(self):
        self.assertEqual(self.service.select([]), [])
