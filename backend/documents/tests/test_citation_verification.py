
"""Tests for citation verification and supporting-source selection."""

from unittest.mock import Mock

import numpy as np
from django.test import SimpleTestCase

from documents.services.citation_verification import (
    CitationVerificationService,
)


class CitationVerificationServiceTests(SimpleTestCase):

    def setUp(self):
        self.model = Mock()
        self.verifier = CitationVerificationService(
            model=self.model
        )

    def test_supported_claim(self):
        self.model.predict.return_value = np.array([
            [0.05, 0.90, 0.05]
        ])

        result = self.verifier.verify(
            claim="RDF uses triples.",
            evidence="RDF uses subject-predicate-object triples.",
        )

        self.assertTrue(result["supported"])
        self.assertEqual(result["label"], "entailment")

    def test_unsupported_claim(self):
        self.model.predict.return_value = np.array([
            [0.05, 0.05, 0.90]
        ])

        result = self.verifier.verify(
            claim="RDF uses triples.",
            evidence="SPARQL is a query language.",
        )

        self.assertFalse(result["supported"])
        self.assertEqual(result["label"], "neutral")

    def test_rejects_empty_claim(self):
        with self.assertRaises(ValueError):
            self.verifier.verify(
                claim=" ",
                evidence="Some evidence.",
            )

    def test_rejects_empty_evidence(self):
        with self.assertRaises(ValueError):
            self.verifier.verify(
                claim="Some claim.",
                evidence=" ",
            )

    def test_finds_supporting_sources(self):
        sources = [
            {
                "source_id": 1,
                "document_id": 5,
                "page_number": 23,
                "chunk_id": 102,
                "text": "The SMART criteria include five components.",
            },
            {
                "source_id": 2,
                "document_id": 5,
                "page_number": 13,
                "chunk_id": 79,
                "text": "KPIs measure organizational performance.",
            },
        ]

        self.model.predict.side_effect = [
            np.array([[0.05, 0.90, 0.05]]),
            np.array([[0.05, 0.05, 0.90]]),
        ]

        matches = self.verifier.find_supporting_sources(
            claim="SMART has five criteria.",
            sources=sources,
        )

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["source_id"], 1)
        self.assertEqual(matches[0]["chunk_id"], 102)

    def test_rejects_invalid_threshold(self):
        with self.assertRaises(ValueError):
            self.verifier.find_supporting_sources(
                claim="Some claim.",
                sources=[],
                min_entailment=1.5,
            )
