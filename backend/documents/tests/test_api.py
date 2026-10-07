import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from documents.models import Document
from documents.tests.utils import create_pdf_bytes


class DocumentAPITests(APITestCase):
    def setUp(self):
        self.temp_media = tempfile.TemporaryDirectory()
        self.override = override_settings(MEDIA_ROOT=self.temp_media.name)
        self.override.enable()

    def tearDown(self):
        self.override.disable()
        self.temp_media.cleanup()

    def test_upload_pdf(self):
        uploaded_file = SimpleUploadedFile(
            "research-paper.pdf",
            create_pdf_bytes("Research paper content"),
            content_type="application/pdf",
        )

        response = self.client.post(
            "/api/documents/",
            {
                "title": "Research Paper",
                "file": uploaded_file,
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Document.objects.count(), 1)

        document = Document.objects.get()

        self.assertEqual(document.title, "Research Paper")
        self.assertEqual(document.original_filename, "research-paper.pdf")
        self.assertEqual(document.status, Document.Status.READY)
        self.assertEqual(document.page_count, 1)
        self.assertEqual(document.pages.count(), 1)

    def test_rejects_non_pdf_upload(self):
        uploaded_file = SimpleUploadedFile(
            "notes.txt",
            b"Not a PDF",
            content_type="text/plain",
        )

        response = self.client.post(
            "/api/documents/",
            {
                "title": "Invalid File",
                "file": uploaded_file,
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Document.objects.count(), 0)
        self.assertIn("file", response.data)

    def test_invalid_pdf_content_is_marked_failed(self):
        uploaded_file = SimpleUploadedFile(
            "broken.pdf",
            b"This has a PDF extension but is not a real PDF.",
            content_type="application/pdf",
        )

        response = self.client.post(
            "/api/documents/",
            {
                "title": "Broken PDF",
                "file": uploaded_file,
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Document.objects.count(), 1)

        document = Document.objects.get()

        self.assertEqual(document.status, Document.Status.FAILED)
        self.assertEqual(document.page_count, 0)
        self.assertEqual(document.pages.count(), 0)
