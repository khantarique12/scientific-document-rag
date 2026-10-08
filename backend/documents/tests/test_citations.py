from django.test import SimpleTestCase

from documents.services.citations import CitationService


class CitationServiceTests(SimpleTestCase):

    def setUp(self):
        self.sources = [
            {"source_id": 1, "page_number": 52},
            {"source_id": 2, "page_number": 76},
            {"source_id": 3, "page_number": 20},
        ]

    def test_extracts_single_citation(self):
        result = CitationService.extract(
            "Ontologies improve interoperability [Source 1].",
            self.sources,
        )

        self.assertEqual(result, [self.sources[0]])

    def test_extracts_multiple_citations(self):
        result = CitationService.extract(
            "First claim [Source 2]. Second claim [Source 1].",
            self.sources,
        )

        self.assertEqual(
            result,
            [self.sources[1], self.sources[0]],
        )

    def test_removes_duplicate_citations(self):
        result = CitationService.extract(
            "First claim [Source 1]. Another claim [Source 1].",
            self.sources,
        )

        self.assertEqual(result, [self.sources[0]])

    def test_ignores_unknown_source_ids(self):
        result = CitationService.extract(
            "A claim [Source 99] and another [Source 2].",
            self.sources,
        )

        self.assertEqual(result, [self.sources[1]])

    def test_returns_empty_when_no_citations(self):
        result = CitationService.extract(
            "An answer without references.",
            self.sources,
        )

        self.assertEqual(result, [])

    def test_handles_empty_sources(self):
        result = CitationService.extract(
            "A claim [Source 1].",
            [],
        )

        self.assertEqual(result, [])