
from django.db import transaction

from documents.models import Document, Page
from documents.services.indexing import IndexingService
from documents.services.page_chunker import PageChunkingService
from documents.services.pdf_extractor import PDFExtractor


class DocumentProcessingService:
    """Coordinate PDF extraction, chunking, and vector indexing."""

    def __init__(
        self,
        extractor=None,
        page_chunker=None,
        indexing_service=None,
    ):
        self.extractor = extractor if extractor is not None else PDFExtractor()
        self.page_chunker = (
            page_chunker if page_chunker is not None
            else PageChunkingService()
        )
        self.indexing_service = (
            indexing_service if indexing_service is not None
            else IndexingService()
        )

    def process(self, document: Document) -> Document:
        document.status = Document.Status.PROCESSING
        document.save(update_fields=["status", "updated_at"])

        try:
            extracted_pages = self.extractor.extract(document.file.path)

            with transaction.atomic():
                document.pages.all().delete()

                pages = Page.objects.bulk_create(
                    [
                        Page(
                            document=document,
                            page_number=page["page_number"],
                            text=page["text"],
                        )
                        for page in extracted_pages
                    ]
                )

                chunks = []

                for page in pages:
                    chunks.extend(self.page_chunker.process(page))

                self.indexing_service.index_chunks(chunks)

                document.page_count = len(pages)
                document.status = Document.Status.READY
                document.save(
                    update_fields=[
                        "page_count",
                        "status",
                        "updated_at",
                    ]
                )

        except Exception:
            document.status = Document.Status.FAILED
            document.save(update_fields=["status", "updated_at"])
            raise

        return document
