from django.test import SimpleTestCase

from documents.services.chunking import ChunkingService


class ChunkingServiceTests(SimpleTestCase):
    def test_short_text_produces_single_chunk(self):
        service = ChunkingService(chunk_size=5, overlap=1)

        chunks = service.split("one two three")

        self.assertEqual(chunks, ["one two three"])

    def test_long_text_produces_overlapping_chunks(self):
        service = ChunkingService(chunk_size=5, overlap=2)

        chunks = service.split(
            "one two three four five six seven eight nine"
        )

        self.assertEqual(
            chunks,
            [
                "one two three four five",
                "four five six seven eight",
                "seven eight nine",
            ],
        )

    def test_empty_text_produces_no_chunks(self):
        service = ChunkingService()

        self.assertEqual(service.split(""), [])
        self.assertEqual(service.split("   "), [])

    def test_overlap_must_be_smaller_than_chunk_size(self):
        with self.assertRaises(ValueError):
            ChunkingService(chunk_size=100, overlap=100)

    def test_chunk_size_must_be_positive(self):
        with self.assertRaises(ValueError):
            ChunkingService(chunk_size=0)

    def test_overlap_cannot_be_negative(self):
        with self.assertRaises(ValueError):
            ChunkingService(chunk_size=100, overlap=-1)