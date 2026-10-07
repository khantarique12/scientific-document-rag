class ChunkingService:
    """Split text into overlapping word-based chunks."""

    def __init__(self, chunk_size=200, overlap=50):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero.")

        if overlap < 0:
            raise ValueError("overlap cannot be negative.")

        if overlap >= chunk_size:
            raise ValueError("overlap must be smaller than chunk_size.")

        self.chunk_size = chunk_size
        self.overlap = overlap

    def split(self, text: str) -> list[str]:
        words = text.split()

        if not words:
            return []

        chunks = []
        step = self.chunk_size - self.overlap

        for start in range(0, len(words), step):
            chunk_words = words[start:start + self.chunk_size]

            if not chunk_words:
                break

            chunks.append(" ".join(chunk_words))

            if start + self.chunk_size >= len(words):
                break

        return chunks