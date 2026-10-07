from pathlib import Path

import pymupdf


class PDFExtractionError(Exception):
    """Raised when a PDF cannot be opened or processed."""


class PDFExtractor:
    """Extract text from a PDF page by page."""

    def extract(self, file_path: str | Path) -> list[dict]:
        file_path = Path(file_path)

        try:
            document = pymupdf.open(file_path)
        except Exception as exc:
            raise PDFExtractionError(
                f"Could not open PDF: {file_path.name}"
            ) from exc

        try:
            pages = []

            for page_index, page in enumerate(document):
                pages.append(
                    {
                        "page_number": page_index + 1,
                        "text": page.get_text("text"),
                    }
                )

            return pages
        except Exception as exc:
            raise PDFExtractionError(
                f"Could not extract text from PDF: {file_path.name}"
            ) from exc
        finally:
            document.close()
