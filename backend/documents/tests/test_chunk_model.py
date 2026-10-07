from django.db import IntegrityError
from django.test import TestCase

from documents.models import Chunk, Document, Page


class ChunkModelTests(TestCase):
    def setUp(self):
        self.document = Document.objects.create(
            title="Scientific Paper",
            original_filename="paper.pdf",
            file="documents/paper.pdf",
        )

        self.page = Page.objects.create(
            document=self.document,
            page_number=1,
            text="This is the full text of page one.",
        )

    def test_chunk_belongs_to_page(self):
        chunk = Chunk.objects.create(
            page=self.page,
            chunk_index=0,
            text="This is a chunk.",
        )

        self.assertEqual(chunk.page, self.page)
        self.assertEqual(self.page.chunks.count(), 1)
        self.assertEqual(chunk.text, "This is a chunk.")

    def test_chunk_string_representation(self):
        chunk = Chunk.objects.create(
            page=self.page,
            chunk_index=0,
            text="Example text",
        )

        self.assertEqual(
            str(chunk),
            "Scientific Paper - page 1 - chunk 0",
        )

    def test_chunk_index_must_be_unique_within_page(self):
        Chunk.objects.create(
            page=self.page,
            chunk_index=0,
            text="First chunk",
        )

        with self.assertRaises(IntegrityError):
            Chunk.objects.create(
                page=self.page,
                chunk_index=0,
                text="Duplicate chunk",
            )

    def test_deleting_page_deletes_its_chunks(self):
        Chunk.objects.create(
            page=self.page,
            chunk_index=0,
            text="Example chunk",
        )

        self.page.delete()

        self.assertEqual(Chunk.objects.count(), 0)

    def test_chunks_are_ordered_by_index(self):
        Chunk.objects.create(
            page=self.page,
            chunk_index=2,
            text="Third chunk",
        )
        Chunk.objects.create(
            page=self.page,
            chunk_index=0,
            text="First chunk",
        )
        Chunk.objects.create(
            page=self.page,
            chunk_index=1,
            text="Second chunk",
        )

        indexes = list(
            self.page.chunks.values_list("chunk_index", flat=True)
        )

        self.assertEqual(indexes, [0, 1, 2])
        