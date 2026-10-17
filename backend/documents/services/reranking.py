
from sentence_transformers import CrossEncoder


class RerankingService:
    """Rerank retrieved chunks using a cross-encoder."""

    MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L6-v2"

    def __init__(self, model=None):
        self.model = model if model is not None else CrossEncoder(
            self.MODEL_NAME
        )

    def rerank(self, query, chunks, limit=5):
        if not query.strip():
            raise ValueError("Query cannot be empty.")

        if limit <= 0:
            raise ValueError("Limit must be greater than zero.")

        if not chunks:
            return []

        pairs = [(query, chunk.text) for chunk in chunks]
        scores = self.model.predict(pairs)

        ranked = sorted(
            zip(chunks, scores),
            key=lambda item: float(item[1]),
            reverse=True,
        )

        return [chunk for chunk, _ in ranked[:limit]]
