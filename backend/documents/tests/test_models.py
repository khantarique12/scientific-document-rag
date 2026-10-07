from django.db import IntegrityError, transaction
from django.test import TestCase

from documents.models import Document, Page


class DocumentModelTests(TestCase):
    def test_document_defaults_to_uploaded_status(self):
        document = Document.objects.create(
            title="Example Paper",
            original_filename="example.pdf",
            file="documents/example.pdf",
        )

        self.assertEqual(document.status, Document.Status.UPLOADED)
        self.assertEqual(document.page_count, 0)
        self.assertEqual(str(document), "Example Paper")


class PageModelTests(TestCase):
    def setUp(self):
        self.document = Document.objects.create(
            title="Example Paper",
            original_filename="example.pdf",
            file="documents/example.pdf",
        )

    def test_page_belongs_to_document(self):
        page = Page.objects.create(
            document=self.document,
            page_number=1,
            text="Scientific content.",
        )

        self.assertEqual(page.document, self.document)
        self.assertEqual(self.document.pages.count(), 1)
        self.assertEqual(str(page), "Example Paper - page 1")

    def test_page_number_is_unique_within_document(self):
        Page.objects.create(
            document=self.document,
            page_number=1,
            text="First version.",
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Page.objects.create(
                    document=self.document,
                    page_number=1,
                    text="Duplicate page.",
                )
