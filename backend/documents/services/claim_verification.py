
"""Verify citations associated with generated answer claims."""

import re

from documents.services.citation_verification import (
    CitationVerificationService,
)


class ClaimVerificationService:
    """Verify cited claims and suggest alternative evidence."""

    CITATION_PATTERN = re.compile(r"\[Source\s+(\d+)\]")

    SENTENCE_PATTERN = re.compile(
        r"(?<=[.!?])\s+(?=[A-Z])"
    )

    BULLET_PATTERN = re.compile(
        r"\s*[•]\s*"
    )

    def __init__(self, citation_verifier=None):
        self.citation_verifier = (
            citation_verifier
            if citation_verifier is not None
            else CitationVerificationService()
        )


    @classmethod
    def _split_claims(cls, text: str) -> list[str]:
        """Split bullet-formatted answers into atomic claims."""

        text = text.strip()

        if not text:
            return []

        if "•" not in text:
            return [text]

        parts = cls.BULLET_PATTERN.split(text)
        claims = []

        for part in parts[1:]:
            part = part.strip()

            if not part:
                continue

            if ":" in part:
                subject, description = part.split(":", 1)

                subject = subject.strip()
                description = description.strip()

                if subject and description:
                    claim = (
                        f"{subject} means "
                        f"{description[0].lower()}"
                        f"{description[1:]}"
                    )
                else:
                    claim = part
            else:
                claim = part

            claims.append(claim)

        return claims or [text]

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

            clean_text = self.CITATION_PATTERN.sub(
                "",
                sentence,
            )

            clean_text = re.sub(
                r"\s+([.,!?;:])",
                r"\1",
                clean_text,
            ).strip()

            claims = self._split_claims(clean_text)

            for claim in claims:
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
