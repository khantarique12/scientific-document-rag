
"""Select diverse, relevant, non-redundant evidence for RAG."""

import re


class ContextSelectionService:
    """Select ranked evidence while filtering weak and overlapping passages."""

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

    def select(
        self,
        chunks,
        limit=5,
        scores=None,
        max_score_gap=None,
        max_context_chars=None,
    ):
        if limit <= 0:
            raise ValueError("Limit must be greater than zero.")

        if max_score_gap is not None and max_score_gap < 0:
            raise ValueError("Score gap cannot be negative.")

        if max_context_chars is not None and max_context_chars <= 0:
            raise ValueError("Context budget must be positive.")

        if scores is not None and len(scores) != len(chunks):
            raise ValueError("Scores must match chunks.")

        if max_score_gap is not None and scores is None:
            raise ValueError("Scores are required for relevance filtering.")

        if not chunks:
            return []

        selected = []
        used_chars = 0

        best_score = max(scores) if scores is not None else None

        for index, chunk in enumerate(chunks):
            if max_score_gap is not None:
                if best_score - scores[index] > max_score_gap:
                    continue

            redundant = any(
                chunk.page.document.id == existing.page.document.id
                and self._has_substantial_overlap(
                    chunk.text,
                    existing.text,
                )
                for existing in selected
            )

            if redundant:
                continue

            chunk_chars = len(chunk.text)

            if (
                max_context_chars is not None
                and selected
                and used_chars + chunk_chars > max_context_chars
            ):
                continue

            selected.append(chunk)
            used_chars += chunk_chars

            if len(selected) >= limit:
                break

        return selected
