
"""Tests for sentence-level citation verification."""

from unittest.mock import Mock

from django.test import SimpleTestCase

from documents.services.claim_verification import (
    ClaimVerificationService,
)


class ClaimVerificationServiceTests(SimpleTestCase):

    def setUp(self):
        self.verifier = Mock()
        self.verifier.verify.return_value = {
            "supported": True,
            "label": "entailment",
            "confidence": 0.95,
        }

        self.service = ClaimVerificationService(
            citation_verifier=self.verifier
        )

        self.sources = [
            {
                "source_id": 1,
                "text": "RDF uses subject-predicate-object triples.",
            },
            {
                "source_id": 2,
                "text": "SPARQL queries RDF datasets.",
            },
        ]

    def test_verifies_two_cited_sentences(self):
        answer = (
            "RDF uses triples [Source 1]. "
            "SPARQL queries RDF datasets [Source 2]."
        )

        results = self.service.verify_answer(
            answer,
            self.sources,
        )

        self.assertEqual(len(results), 2)
        self.assertTrue(all(item["supported"] for item in results))

    def test_extracts_clean_claim_text(self):
        results = self.service.verify_answer(
            "RDF uses triples [Source 1].",
            self.sources,
        )

        self.assertEqual(
            results[0]["claim"],
            "RDF uses triples.",
        )

    def test_detects_unsupported_claim(self):
        self.verifier.verify.return_value = {
            "supported": False,
            "label": "neutral",
            "confidence": 0.98,
        }

        results = self.service.verify_answer(
            "RDF uses JSON objects [Source 1].",
            self.sources,
        )

        self.assertFalse(results[0]["supported"])
        self.assertEqual(results[0]["label"], "neutral")

    def test_handles_missing_source(self):
        results = self.service.verify_answer(
            "RDF uses triples [Source 99].",
            self.sources,
        )

        self.assertFalse(results[0]["supported"])
        self.assertEqual(
            results[0]["label"],
            "missing_source",
        )

        self.verifier.verify.assert_not_called()

    def test_handles_multiple_citations(self):
        results = self.service.verify_answer(
            "RDF uses triples [Source 1] [Source 2].",
            self.sources,
        )

        self.assertEqual(len(results), 2)
        self.assertEqual(
            [item["source_id"] for item in results],
            [1, 2],
        )

    def test_deduplicates_citations(self):
        results = self.service.verify_answer(
            "RDF uses triples [Source 1] [Source 1].",
            self.sources,
        )

        self.assertEqual(len(results), 1)

    def test_handles_answer_without_citations(self):
        results = self.service.verify_answer(
            "RDF uses triples.",
            self.sources,
        )

        self.assertEqual(results, [])
        self.verifier.verify.assert_not_called()

    def test_handles_empty_answer(self):
        results = self.service.verify_answer(
            "",
            self.sources,
        )

        self.assertEqual(results, [])

    
    def test_suggests_alternative_for_unsupported_claim(self):
        self.verifier.verify.return_value = {
            "supported": False,
            "label": "neutral",
            "confidence": 0.98,
        }

        self.verifier.find_supporting_sources.return_value = [
            {
                "source_id": 2,
                "document_id": 5,
                "page_number": 23,
                "chunk_id": 102,
                "entailment_score": 0.4738,
            }
        ]

        results = self.service.verify_answer(
            "SMART has five criteria [Source 1].",
            self.sources,
        )

        self.assertFalse(results[0]["supported"])
        self.assertEqual(
            results[0]["alternative_sources"][0]["source_id"],
            2,
        )

        self.verifier.find_supporting_sources.assert_called_once()
        self.assertEqual(
            self.verifier.find_supporting_sources.call_args.kwargs[
                "min_entailment"
            ],
            0.4,
        )

    def test_does_not_search_alternatives_when_supported(self):
        results = self.service.verify_answer(
            "RDF uses triples [Source 1].",
            self.sources,
        )

        self.assertTrue(results[0]["supported"])
        self.assertEqual(
            results[0]["alternative_sources"],
            [],
        )

        self.verifier.find_supporting_sources.assert_not_called()
