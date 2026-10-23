
"""Ranking metrics for evaluating retrieval quality."""


def recall_at_k(
    retrieved_ids: list[int],
    relevant_ids: set[int],
    k: int,
) -> float:
    """Fraction of relevant chunks retrieved within top k."""

    if k <= 0:
        raise ValueError("k must be positive.")

    if not relevant_ids:
        raise ValueError("Relevant IDs cannot be empty.")

    top_k = set(retrieved_ids[:k])

    return len(top_k & relevant_ids) / len(relevant_ids)


def reciprocal_rank(
    retrieved_ids: list[int],
    relevant_ids: set[int],
) -> float:
    """Reciprocal rank of the first relevant retrieved chunk."""

    if not relevant_ids:
        raise ValueError("Relevant IDs cannot be empty.")

    for rank, chunk_id in enumerate(retrieved_ids, start=1):
        if chunk_id in relevant_ids:
            return 1.0 / rank

    return 0.0


def mean_reciprocal_rank(
    rankings: list[list[int]],
    relevant_sets: list[set[int]],
) -> float:
    """Mean reciprocal rank across evaluation questions."""

    if not rankings:
        raise ValueError("Rankings cannot be empty.")

    if len(rankings) != len(relevant_sets):
        raise ValueError(
            "Rankings and relevant sets must have equal lengths."
        )

    scores = [
        reciprocal_rank(retrieved, relevant)
        for retrieved, relevant in zip(
            rankings,
            relevant_sets,
        )
    ]

    return sum(scores) / len(scores)
