from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from documents.api.serializers import DocumentSerializer
from documents.models import Document


class DocumentSerializerTests(TestCase):
    def test_accepts_pdf_file(self):
        uploaded_file = SimpleUploadedFile(
            "paper.pdf",
            b"%PDF-1.4 test content",
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
        self.assertEqual(document.status, Document.Status.UPLOADED)
        self.assertEqual(document.page_count, 0)

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