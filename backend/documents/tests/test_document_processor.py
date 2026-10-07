from unittest.mock import Mock

from django.test import TestCase

from documents.models import Document
from documents.services.document_processor import DocumentProcessingService
from documents.services.pdf_extractor import PDFExtractionError


class DocumentProcessingServiceTests(TestCase):
    def setUp(self):
        self.document = Document.objects.create(
            title="Scientific Paper",
            original_filename="paper.pdf",
            file="documents/paper.pdf",
        )

    def test_process_creates_pages_and_marks_document_ready(self):
        extractor = Mock()
        extractor.extract.return_value = [
            {
                "page_number": 1,
                "text": "Introduction",
            },
            {
                "page_number": 2,
                "text": "Results",
            },
        ]

        service = DocumentProcessingService(extractor=extractor)

        service.process(self.document)

        self.document.refresh_from_db()

        self.assertEqual(self.document.status, Document.Status.READY)
        self.assertEqual(self.document.page_count, 2)
        self.assertEqual(self.document.pages.count(), 2)

        self.assertEqual(
            self.document.pages.get(page_number=1).text,
            "Introduction",
        )
        self.assertEqual(
            self.document.pages.get(page_number=2).text,
            "Results",
        )

        extractor.extract.assert_called_once_with(self.document.file.path)

    def test_process_marks_document_failed_when_extraction_fails(self):
        extractor = Mock()
        extractor.extract.side_effect = PDFExtractionError(
            "Could not extract PDF."
        )

        service = DocumentProcessingService(extractor=extractor)

        with self.assertRaises(PDFExtractionError):
            service.process(self.document)

        self.document.refresh_from_db()

        self.assertEqual(self.document.status, Document.Status.FAILED)
        self.assertEqual(self.document.page_count, 0)
        self.assertEqual(self.document.pages.count(), 0)
