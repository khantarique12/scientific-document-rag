from unittest.mock import Mock

from django.test import TestCase

from documents.models import Document, Page
from documents.services.page_chunker import PageChunkingService


class PageChunkingServiceTests(TestCase):
    def setUp(self):
        self.document = Document.objects.create(
            title="Scientific Paper",
            original_filename="paper.pdf",
            file="documents/paper.pdf",
        )

        self.page = Page.objects.create(
            document=self.document,
            page_number=1,
            text="Example page text",
        )

    def test_process_creates_chunks_for_page(self):
        chunker = Mock()
        chunker.split.return_value = [
            "First chunk",
            "Second chunk",
        ]

        service = PageChunkingService(chunker=chunker)
        chunks = service.process(self.page)

        self.assertEqual(len(chunks), 2)
        self.assertEqual(self.page.chunks.count(), 2)

        first_chunk = self.page.chunks.get(chunk_index=0)
        second_chunk = self.page.chunks.get(chunk_index=1)

        self.assertEqual(first_chunk.text, "First chunk")
        self.assertEqual(second_chunk.text, "Second chunk")

        chunker.split.assert_called_once_with(self.page.text)

    def test_process_replaces_existing_chunks(self):
        chunker = Mock()
        chunker.split.return_value = ["Original chunk"]

        service = PageChunkingService(chunker=chunker)
        service.process(self.page)

        self.assertEqual(self.page.chunks.count(), 1)

        chunker.split.return_value = [
            "New first chunk",
            "New second chunk",
        ]

        service.process(self.page)

        self.assertEqual(self.page.chunks.count(), 2)
        self.assertFalse(
            self.page.chunks.filter(text="Original chunk").exists()
        )

    def test_empty_page_creates_no_chunks(self):
        self.page.text = ""
        self.page.save(update_fields=["text"])

        service = PageChunkingService()
        chunks = service.process(self.page)

        self.assertEqual(chunks, [])
        self.assertEqual(self.page.chunks.count(), 0)