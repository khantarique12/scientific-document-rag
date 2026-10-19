
from django.test import SimpleTestCase

from documents.services.citation_correction import (
    CitationCorrectionService,
)


class CitationCorrectionServiceTests(SimpleTestCase):

    def setUp(self):
        self.service = CitationCorrectionService(
            min_entailment=0.85
        )

    def test_corrects_single_high_confidence_alternative(self):
        answer = "KPIs follow SMART criteria. [Source 2]"

        verification = [{
            "claim": "KPIs follow SMART criteria.",
            "source_id": 2,
            "supported": False,
            "alternative_sources": [{
                "source_id": 1,
                "entailment_score": 0.94,
            }],
        }]

        result = self.service.correct(answer, verification)

        self.assertEqual(
            result["answer"],
            "KPIs follow SMART criteria. [Source 1]",
        )
        self.assertEqual(len(result["corrections"]), 1)

    def test_preserves_citation_below_threshold(self):
        answer = "SMART has five criteria. [Source 2]"

        verification = [{
            "claim": "SMART has five criteria.",
            "source_id": 2,
            "supported": False,
            "alternative_sources": [{
                "source_id": 1,
                "entailment_score": 0.4738,
            }],
        }]

        result = self.service.correct(answer, verification)

        self.assertEqual(result["answer"], answer)
        self.assertEqual(result["corrections"], [])

    def test_preserves_supported_citation(self):
        answer = "A KPI measures performance. [Source 1]"

        verification = [{
            "claim": "A KPI measures performance.",
            "source_id": 1,
            "supported": True,
            "alternative_sources": [{
                "source_id": 2,
                "entailment_score": 0.99,
            }],
        }]

        result = self.service.correct(answer, verification)

        self.assertEqual(result["answer"], answer)

    def test_preserves_ambiguous_alternatives(self):
        answer = "KPIs measure goals. [Source 2]"

        verification = [{
            "claim": "KPIs measure goals.",
            "source_id": 2,
            "supported": False,
            "alternative_sources": [
                {
                    "source_id": 1,
                    "entailment_score": 0.95,
                },
                {
                    "source_id": 3,
                    "entailment_score": 0.91,
                },
            ],
        }]

        result = self.service.correct(answer, verification)

        self.assertEqual(result["answer"], answer)

    def test_preserves_repeated_citations(self):
        answer = (
            "First claim. [Source 2] "
            "Second claim. [Source 2]"
        )

        verification = [{
            "claim": "First claim.",
            "source_id": 2,
            "supported": False,
            "alternative_sources": [{
                "source_id": 1,
                "entailment_score": 0.96,
            }],
        }]

        result = self.service.correct(answer, verification)

        self.assertEqual(result["answer"], answer)

    def test_rejects_invalid_threshold(self):
        with self.assertRaises(ValueError):
            CitationCorrectionService(min_entailment=1.5)

    def test_preserves_citation_when_claim_does_not_match(self):
        answer = "Claim A. [Source 2]"

        verification = [{
            "claim": "Different claim.",
            "source_id": 2,
            "supported": False,
            "alternative_sources": [{
                "source_id": 1,
                "entailment_score": 0.95,
            }],
        }]

        result = self.service.correct(answer, verification)

        self.assertEqual(result["answer"], answer)
        self.assertEqual(result["corrections"], [])


    def test_preserves_citation_when_claim_is_missing(self):
        answer = "Claim A. [Source 2]"

        verification = [{
            "source_id": 2,
            "supported": False,
            "alternative_sources": [{
                "source_id": 1,
                "entailment_score": 0.95,
            }],
        }]

        result = self.service.correct(answer, verification)

        self.assertEqual(result["answer"], answer)
        self.assertEqual(result["corrections"], [])