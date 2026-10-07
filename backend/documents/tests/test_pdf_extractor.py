import tempfile
from pathlib import Path

import pymupdf
from django.test import SimpleTestCase

from documents.services.pdf_extractor import (
    PDFExtractionError,
    PDFExtractor,
)


class PDFExtractorTests(SimpleTestCase):
    def setUp(self):
        self.extractor = PDFExtractor()

    def test_extracts_text_from_multiple_pages(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "test.pdf"

            document = pymupdf.open()

            page_one = document.new_page()
            page_one.insert_text(
                (72, 72),
                "Introduction to scientific RAG",
            )

            page_two = document.new_page()
            page_two.insert_text(
                (72, 72),
                "Results and discussion",
            )

            document.save(pdf_path)
            document.close()

            pages = self.extractor.extract(pdf_path)

        self.assertEqual(len(pages), 2)

        self.assertEqual(pages[0]["page_number"], 1)
        self.assertIn(
            "Introduction to scientific RAG",
            pages[0]["text"],
        )

        self.assertEqual(pages[1]["page_number"], 2)
        self.assertIn(
            "Results and discussion",
            pages[1]["text"],
        )

    def test_raises_error_for_invalid_pdf(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "invalid.pdf"
            pdf_path.write_text("This is not a PDF.")

            with self.assertRaises(PDFExtractionError):
                self.extractor.extract(pdf_path)
