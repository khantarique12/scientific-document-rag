
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

        self.extractor = Mock()
        self.page_chunker = Mock()
        self.indexing_service = Mock()

        self.service = DocumentProcessingService(
            extractor=self.extractor,
            page_chunker=self.page_chunker,
            indexing_service=self.indexing_service,
        )

    def test_process_creates_pages_indexes_chunks_and_marks_ready(self):
        self.extractor.extract.return_value = [
            {"page_number": 1, "text": "Introduction"},
            {"page_number": 2, "text": "Results"},
        ]

        chunk1 = Mock()
        chunk2 = Mock()

        self.page_chunker.process.side_effect = [
            [chunk1],
            [chunk2],
        ]

        self.service.process(self.document)

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

        self.extractor.extract.assert_called_once_with(
            self.document.file.path
        )

        self.assertEqual(self.page_chunker.process.call_count, 2)

        processed_page_numbers = [
            call.args[0].page_number
            for call in self.page_chunker.process.call_args_list
        ]

        self.assertEqual(processed_page_numbers, [1, 2])

        self.indexing_service.index_chunks.assert_called_once_with(
            [chunk1, chunk2]
        )

    def test_process_marks_failed_when_extraction_fails(self):
        self.extractor.extract.side_effect = PDFExtractionError(
            "Could not extract PDF."
        )

        with self.assertRaises(PDFExtractionError):
            self.service.process(self.document)

        self.document.refresh_from_db()

        self.assertEqual(self.document.status, Document.Status.FAILED)
        self.assertEqual(self.document.page_count, 0)
        self.assertEqual(self.document.pages.count(), 0)

        self.indexing_service.index_chunks.assert_not_called()

    def test_process_marks_failed_when_indexing_fails(self):
        self.extractor.extract.return_value = [
            {"page_number": 1, "text": "Introduction"}
        ]

        self.page_chunker.process.return_value = [Mock()]

        self.indexing_service.index_chunks.side_effect = RuntimeError(
            "Embedding generation failed."
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "Embedding generation failed",
        ):
            self.service.process(self.document)

        self.document.refresh_from_db()

        self.assertEqual(self.document.status, Document.Status.FAILED)
        self.assertEqual(self.document.page_count, 0)
        self.assertEqual(self.document.pages.count(), 0)

    def test_process_handles_document_without_chunks(self):
        self.extractor.extract.return_value = [
            {"page_number": 1, "text": ""}
        ]

        self.page_chunker.process.return_value = []

        self.service.process(self.document)

        self.document.refresh_from_db()

        self.assertEqual(self.document.status, Document.Status.READY)

        self.indexing_service.index_chunks.assert_called_once_with([])
