from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from documents.tests.utils import create_pdf_bytes
from documents.api.serializers import DocumentSerializer
from documents.models import Document
from unittest.mock import patch

class DocumentSerializerTests(TestCase):

    @patch(
    "documents.services.document_processor.IndexingService"
    )
    def test_accepts_pdf_file(self, mock_indexing_service):
        uploaded_file = SimpleUploadedFile(
            "paper.pdf",
            create_pdf_bytes("Scientific paper content"),
            content_type="application/pdf",
        )

        serializer = DocumentSerializer(
            data={
                "title": "Example Scientific Paper",
                "file": uploaded_file,
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        document = serializer.save()

        self.assertEqual(document.title, "Example Scientific Paper")
        self.assertEqual(document.original_filename, "paper.pdf")
        self.assertEqual(document.status, Document.Status.READY)
        self.assertEqual(document.page_count, 1)
        self.assertEqual(document.pages.count(), 1)

    def test_rejects_non_pdf_file(self):
        uploaded_file = SimpleUploadedFile(
            "notes.txt",
            b"This is not a PDF.",
            content_type="text/plain",
        )

        serializer = DocumentSerializer(
            data={
                "title": "Invalid Document",
                "file": uploaded_file,
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("file", serializer.errors)
