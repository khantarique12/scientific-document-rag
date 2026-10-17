
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from pgvector.django import CosineDistance

from documents.models import Chunk
from documents.services.embedding import EmbeddingService


class RetrievalService:
    """Retrieve document chunks using semantic and keyword search."""

    CANDIDATE_LIMIT = 30
    RRF_K = 60

    def __init__(self, embedding_service=None):
        self.embedding_service = embedding_service or EmbeddingService()

    def search(
        self,
        query: str,
        limit: int = 5,
        document_id: int | None = None,
        strategy: str = "hybrid",
    ) -> list[Chunk]:
        if not query.strip():
            raise ValueError("Query cannot be empty.")

        if limit <= 0:
            raise ValueError("Limit must be greater than zero.")

        if strategy not in {"semantic", "hybrid"}:
            raise ValueError("Invalid retrieval strategy.")

        queryset = Chunk.objects.filter(embedding__isnull=False)

        if document_id is not None:
            queryset = queryset.filter(page__document_id=document_id)

        query_embedding = self.embedding_service.embed(query)

        candidate_limit = max(limit, self.CANDIDATE_LIMIT)

        semantic_results = list(
            queryset
            .select_related("page", "page__document")
            .annotate(
                distance=CosineDistance("embedding", query_embedding)
            )
            .order_by("distance", "id")[:candidate_limit]
        )

        if strategy == "semantic":
            return semantic_results[:limit]

        search_vector = SearchVector("text", config="english")
        search_query = SearchQuery(
            query,
            config="english",
            search_type="websearch",
        )

        keyword_results = list(
            queryset
            .select_related("page", "page__document")
            .annotate(
                search_rank=SearchRank(search_vector, search_query)
            )
            .filter(search_rank__gt=0)
            .order_by("-search_rank", "id")[:candidate_limit]
        )

        scores = {}
        chunks = {}

        for rank, chunk in enumerate(semantic_results, start=1):
            chunks[chunk.id] = chunk
            scores[chunk.id] = (
                scores.get(chunk.id, 0)
                + 1 / (self.RRF_K + rank)
            )

        for rank, chunk in enumerate(keyword_results, start=1):
            if chunk.id not in chunks:
                chunks[chunk.id] = chunk

            scores[chunk.id] = (
                scores.get(chunk.id, 0)
                + 1 / (self.RRF_K + rank)
            )

        ranked_ids = sorted(
            scores,
            key=lambda chunk_id: (-scores[chunk_id], chunk_id),
        )

        # RAGService expects a cosine-distance annotation.
        # Keyword-only candidates also need this attribute.
        for chunk_id in ranked_ids[:limit]:
            chunk = chunks[chunk_id]

            if not hasattr(chunk, "distance"):
                chunk.distance = None

        # Return semantic-distance values for all selected chunks.
        # This preserves compatibility with existing RAG responses.
        from pgvector.django import CosineDistance as Distance

        selected_ids = ranked_ids[:limit]
        selected_chunks = {
            chunk.id: chunk
            for chunk in Chunk.objects.filter(
                id__in=selected_ids
            )
            .select_related("page", "page__document")
            .annotate(
                distance=Distance("embedding", query_embedding)
            )
        }

        return [selected_chunks[chunk_id] for chunk_id in selected_ids]
