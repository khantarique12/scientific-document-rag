from django.db import transaction

from documents.models import Document, Page
from documents.services.page_chunker import PageChunkingService
from documents.services.pdf_extractor import PDFExtractionError, PDFExtractor


class DocumentProcessingService:
    """Coordinate PDF extraction, page persistence, and chunking."""

    def __init__(self, extractor=None, page_chunker=None):
        self.extractor = extractor or PDFExtractor()
        self.page_chunker = page_chunker or PageChunkingService()

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

                for page in pages:
                    self.page_chunker.process(page)

                document.page_count = len(pages)
                document.status = Document.Status.READY
                document.save(
                    update_fields=[
                        "page_count",
                        "status",
                        "updated_at",
                    ]
                )

        except PDFExtractionError:
            document.status = Document.Status.FAILED
            document.save(update_fields=["status", "updated_at"])
            raise

        return document