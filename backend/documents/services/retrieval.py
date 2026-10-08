from pgvector.django import CosineDistance

from documents.models import Chunk
from documents.services.embedding import EmbeddingService


class RetrievalService:
    """Retrieve document chunks by semantic similarity."""

    def __init__(self, embedding_service=None):
        self.embedding_service = embedding_service or EmbeddingService()

    def search(
        self,
        query: str,
        limit: int = 5,
    ) -> list[Chunk]:
        if not query.strip():
            raise ValueError("Query cannot be empty.")

        if limit <= 0:
            raise ValueError("Limit must be greater than zero.")

        query_embedding = self.embedding_service.embed(query)

        return list(
            Chunk.objects
            .filter(embedding__isnull=False)
            .select_related("page", "page__document")
            .annotate(
                distance=CosineDistance(
                    "embedding",
                    query_embedding,
                )
            )
            .order_by("distance")[:limit]
        )