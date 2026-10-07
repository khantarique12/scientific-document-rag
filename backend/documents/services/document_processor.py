from django.db import transaction

from documents.models import Document, Page
from documents.services.pdf_extractor import PDFExtractionError, PDFExtractor


class DocumentProcessingService:
    """Coordinate PDF extraction and persistence of document pages."""

    def __init__(self, extractor=None):
        self.extractor = extractor or PDFExtractor()

    def process(self, document: Document) -> Document:
        document.status = Document.Status.PROCESSING
        document.save(update_fields=["status", "updated_at"])

        try:
            extracted_pages = self.extractor.extract(document.file.path)

            with transaction.atomic():
                document.pages.all().delete()

                Page.objects.bulk_create(
                    [
                        Page(
                            document=document,
                            page_number=page["page_number"],
                            text=page["text"],
                        )
                        for page in extracted_pages
                    ]
                )

                document.page_count = len(extracted_pages)
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
