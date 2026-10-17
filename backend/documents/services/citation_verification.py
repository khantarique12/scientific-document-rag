
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

        # NLI expects the premise first, hypothesis second.
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
