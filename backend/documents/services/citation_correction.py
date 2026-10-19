
"""Conservatively correct unsupported answer citations."""

import re


class CitationCorrectionService:
    """Replace citations only when stronger evidence is available."""

    CITATION_PATTERN = re.compile(r"\[Source\s+(\d+)\]")

    def __init__(self, min_entailment=0.85):
        if not 0 <= min_entailment <= 1:
            raise ValueError(
                "min_entailment must be between 0 and 1."
            )

        self.min_entailment = min_entailment

    def correct(
        self,
        answer: str,
        verification_results: list[dict],
    ) -> dict:
        """Return an answer with eligible citation replacements.

        A replacement is permitted only when:
        - The original citation was classified as unsupported.
        - Exactly one alternative meets the configured threshold.
        - The cited source ID occurs exactly once in the answer.

        Otherwise, preserve the original citation.
        """

        corrected_answer = answer
        corrections = []

        for result in verification_results:
            if result["supported"]:
                continue

            original_id = result["source_id"]

            alternatives = [
                alternative
                for alternative in result.get(
                    "alternative_sources", []
                )
                if alternative["source_id"] != original_id
                and alternative["entailment_score"]
                >= self.min_entailment
            ]

            if len(alternatives) != 1:
                continue

            pattern = re.compile(
                rf"\[Source\s+{original_id}\]"
            )

            matches = list(pattern.finditer(corrected_answer))

            if len(matches) != 1:
                continue

            # Ensure the citation belongs to the verified claim.
            claim = result.get("claim", "").strip()

            if not claim:
                continue

            citation_start = matches[0].start()

            preceding_text = corrected_answer[:citation_start].rstrip()

            if not preceding_text.endswith(claim):
                continue

            replacement_id = alternatives[0]["source_id"]

            corrected_answer = pattern.sub(
                f"[Source {replacement_id}]",
                corrected_answer,
                count=1,
            )

            corrections.append({
                "original_source_id": original_id,
                "replacement_source_id": replacement_id,
                "entailment_score": alternatives[0][
                    "entailment_score"
                ],
            })

        return {
            "answer": corrected_answer,
            "corrections": corrections,
        }
