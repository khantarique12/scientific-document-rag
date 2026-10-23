
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


    def test_filters_chunks_with_large_score_gap(self):
        chunks = [
            self.make_chunk(102, "The five SMART criteria."),
            self.make_chunk(198, "General KPI discussion."),
            self.make_chunk(246, "Machine learning KPI forecasting."),
        ]

        result = self.service.select(
            chunks,
            limit=5,
            scores=[4.3875, 2.3326, 2.2616],
            max_score_gap=1.5,
        )

        self.assertEqual(result, [chunks[0]])

    def test_preserves_multiple_relevant_sources(self):
        chunks = [
            self.make_chunk(1, "RDF supports semantic data.", document_id=1),
            self.make_chunk(2, "OWL supports ontology modeling.", document_id=2),
            self.make_chunk(3, "Unrelated background.", document_id=3),
        ]

        result = self.service.select(
            chunks,
            scores=[5.0, 4.7, 1.0],
            max_score_gap=1.5,
        )

        self.assertEqual(result, chunks[:2])

    def test_respects_context_budget(self):
        chunks = [
            self.make_chunk(1, "A" * 100),
            self.make_chunk(2, "B" * 100),
            self.make_chunk(3, "C" * 100),
        ]

        result = self.service.select(
            chunks,
            max_context_chars=220,
        )

        self.assertEqual(result, chunks[:2])

    def test_rejects_mismatched_scores(self):
        chunks = [self.make_chunk(1, "Scientific evidence.")]

        with self.assertRaises(ValueError):
            self.service.select(
                chunks,
                scores=[5.0, 4.0],
                max_score_gap=1.5,
            )

    def test_rejects_gap_without_scores(self):
        chunks = [self.make_chunk(1, "Scientific evidence.")]

        with self.assertRaises(ValueError):
            self.service.select(
                chunks,
                max_score_gap=1.5,
            )
