
"""Verify whether document evidence supports generated claims."""

import numpy as np
from sentence_transformers import CrossEncoder


class CitationVerificationService:
    """Evaluate claim-evidence support using an NLI model."""

    MODEL_NAME = "cross-encoder/nli-MiniLM2-L6-H768"

    LABELS = (
        "contradiction",
        "entailment",
        "neutral",
    )

    def __init__(self, model=None):
        self.model = (
            model
            if model is not None
            else CrossEncoder(self.MODEL_NAME)
        )

    def verify(self, claim: str, evidence: str) -> dict:
        """Estimate whether the evidence entails the claim."""

        if not claim.strip():
            raise ValueError("Claim cannot be empty.")

        if not evidence.strip():
            raise ValueError("Evidence cannot be empty.")

        # NLI expects premise first and hypothesis second.
        scores = self.model.predict(
            [(evidence, claim)],
            apply_softmax=True,
        )

        probabilities = np.asarray(scores)[0]

        predicted_index = int(np.argmax(probabilities))
        predicted_label = self.LABELS[predicted_index]

        return {
            "supported": predicted_label == "entailment",
            "label": predicted_label,
            "confidence": float(probabilities[predicted_index]),
            "probabilities": {
                label: float(probability)
                for label, probability in zip(
                    self.LABELS,
                    probabilities,
                )
            },
        }

    def find_supporting_sources(
        self,
        claim: str,
        sources: list[dict],
        min_entailment: float = 0.5,
    ) -> list[dict]:
        """Return sources ranked by estimated entailment."""

        if not 0 <= min_entailment <= 1:
            raise ValueError(
                "min_entailment must be between 0 and 1."
            )

        if not claim.strip():
            raise ValueError("Claim cannot be empty.")

        matches = []

        for source in sources:
            result = self.verify(
                claim=claim,
                evidence=source["text"],
            )

            entailment = result["probabilities"]["entailment"]

            if (
                result["label"] == "entailment"
                and entailment >= min_entailment
            ):
                matches.append({
                    "source_id": source["source_id"],
                    "document_id": source["document_id"],
                    "page_number": source["page_number"],
                    "chunk_id": source["chunk_id"],
                    "entailment_score": round(entailment, 4),
                })

        return sorted(
            matches,
            key=lambda item: item["entailment_score"],
            reverse=True,
        )
