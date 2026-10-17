
"""Verify citations associated with generated answer claims."""

import re

from documents.services.citation_verification import (
    CitationVerificationService,
)


class ClaimVerificationService:
    """Verify cited sentences and suggest alternative evidence."""

    CITATION_PATTERN = re.compile(r"\[Source\s+(\d+)\]")

    SENTENCE_PATTERN = re.compile(
        r"(?<=[.!?])\s+(?=[A-Z])"
    )

    def __init__(self, citation_verifier=None):
        self.citation_verifier = (
            citation_verifier
            if citation_verifier is not None
            else CitationVerificationService()
        )

    def verify_answer(
        self,
        answer: str,
        sources: list[dict],
    ) -> list[dict]:
        """Verify claim-source pairs found in the answer."""

        source_lookup = {
            source["source_id"]: source
            for source in sources
        }

        results = []

        for sentence in self.SENTENCE_PATTERN.split(
            answer.strip()
        ):
            cited_ids = [
                int(match)
                for match in self.CITATION_PATTERN.findall(
                    sentence
                )
            ]

            if not cited_ids:
                continue

            claim = self.CITATION_PATTERN.sub(
                "",
                sentence,
            )

            claim = re.sub(
                r"\s+([.,!?;:])",
                r"\1",
                claim,
            ).strip()

            if not claim:
                continue

            for source_id in dict.fromkeys(cited_ids):
                source = source_lookup.get(source_id)

                if source is None:
                    results.append({
                        "claim": claim,
                        "source_id": source_id,
                        "supported": False,
                        "label": "missing_source",
                        "confidence": None,
                        "alternative_sources": [],
                    })
                    continue

                verification = self.citation_verifier.verify(
                    claim=claim,
                    evidence=source["text"],
                )

                alternative_sources = []

                if not verification["supported"]:
                    candidates = [
                        candidate
                        for candidate in sources
                        if candidate["source_id"] != source_id
                    ]

                    # Use alternative-source lookup only when
                    # the injected verifier supports it.
                    find_alternatives = getattr(
                        self.citation_verifier,
                        "find_supporting_sources",
                        None,
                    )

                    if callable(find_alternatives):
                        found = find_alternatives(
                            claim=claim,
                            sources=candidates,
                            min_entailment=0.4,
                        )

                        if found is not None:
                            alternative_sources = found

                results.append({
                    "claim": claim,
                    "source_id": source_id,
                    "supported": verification["supported"],
                    "label": verification["label"],
                    "confidence": verification["confidence"],
                    "alternative_sources": alternative_sources,
                })

        return results
