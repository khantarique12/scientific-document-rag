from django.db import transaction

from documents.models import Chunk
from documents.services.embedding import EmbeddingService


class IndexingService:
    """Generate and persist embeddings for document chunks."""

    DEFAULT_BATCH_SIZE = 32

    def __init__(self, embedding_service=None):
        self.embedding_service = embedding_service or EmbeddingService()

    def index_chunk(self, chunk: Chunk) -> Chunk:
        embedding = self.embedding_service.embed(chunk.text)

        chunk.embedding = embedding
        chunk.save(update_fields=["embedding"])

        return chunk

    def index_chunks(
        self,
        chunks: list[Chunk],
        batch_size: int = DEFAULT_BATCH_SIZE,
    ) -> list[Chunk]:
        if batch_size <= 0:
            raise ValueError("batch_size must be greater than zero.")

        if not chunks:
            return []

        for start in range(0, len(chunks), batch_size):
            batch = chunks[start:start + batch_size]

            embeddings = self.embedding_service.embed_batch(
                [chunk.text for chunk in batch]
            )

            if len(embeddings) != len(batch):
                raise ValueError(
                    "Number of embeddings does not match number of chunks."
                )

            for chunk, embedding in zip(batch, embeddings):
                chunk.embedding = embedding

            with transaction.atomic():
                Chunk.objects.bulk_update(
                    batch,
                    ["embedding"],
                )

        return chunks