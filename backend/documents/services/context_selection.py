
"""Select diverse, non-redundant evidence for RAG."""

import re


class ContextSelectionService:
    """Remove passages containing substantial overlapping text."""

    MIN_OVERLAP_WORDS = 20

    @staticmethod
    def _tokens(text):
        return re.findall(r"\w+", text.lower())

    @classmethod
    def _has_substantial_overlap(cls, text_a, text_b):
        tokens_a = cls._tokens(text_a)
        tokens_b = cls._tokens(text_b)

        if not tokens_a or not tokens_b:
            return False

        # Use the shorter passage to reduce comparisons.
        if len(tokens_a) > len(tokens_b):
            tokens_a, tokens_b = tokens_b, tokens_a

        window_size = min(
            cls.MIN_OVERLAP_WORDS,
            len(tokens_a),
        )

        if window_size < cls.MIN_OVERLAP_WORDS:
            return False

        windows_a = {
            tuple(tokens_a[i:i + window_size])
            for i in range(len(tokens_a) - window_size + 1)
        }

        for i in range(len(tokens_b) - window_size + 1):
            window = tuple(tokens_b[i:i + window_size])

            if window in windows_a:
                return True

        return False

    def select(self, chunks, limit=5):
        if limit <= 0:
            raise ValueError("Limit must be greater than zero.")

        selected = []

        for chunk in chunks:
            redundant = any(
                chunk.page.document.id
                == existing.page.document.id
                and self._has_substantial_overlap(
                    chunk.text,
                    existing.text,
                )
                for existing in selected
            )

            if not redundant:
                selected.append(chunk)

            if len(selected) >= limit:
                break

        return selected
