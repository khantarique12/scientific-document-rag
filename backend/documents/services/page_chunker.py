from django.db import transaction

from documents.models import Chunk, Page
from documents.services.chunking import ChunkingService


class PageChunkingService:
    """Create and persist chunks for a document page."""

    def __init__(self, chunker=None):
        self.chunker = chunker or ChunkingService()

    def process(self, page: Page) -> list[Chunk]:
        chunk_texts = self.chunker.split(page.text)

        with transaction.atomic():
            page.chunks.all().delete()

            chunks = Chunk.objects.bulk_create(
                [
                    Chunk(
                        page=page,
                        chunk_index=index,
                        text=text,
                    )
                    for index, text in enumerate(chunk_texts)
                ]
            )

        return chunks