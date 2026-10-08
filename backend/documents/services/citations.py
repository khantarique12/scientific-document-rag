"""Utilities for extracting and resolving source citations."""

import re


class CitationService:
    """Extract valid source references from generated answers."""

    CITATION_PATTERN = re.compile(r"\[Source\s+(\d+)\]")

    @classmethod
    def extract(cls, answer: str, sources: list[dict]) -> list[dict]:
        """Return referenced sources in their first-cited order."""

        source_lookup = {
            source["source_id"]: source
            for source in sources
        }

        citations = []
        seen = set()

        for match in cls.CITATION_PATTERN.finditer(answer):
            source_id = int(match.group(1))

            if source_id in seen:
                continue

            if source_id not in source_lookup:
                continue

            citations.append(source_lookup[source_id])
            seen.add(source_id)

        return citations