
"""Tests for retrieval evaluation metrics."""

from django.test import SimpleTestCase

from documents.evaluation.metrics import (
    hit_at_k,
    mean_reciprocal_rank,
    recall_at_k,
    reciprocal_rank,
)


class RetrievalMetricsTests(SimpleTestCase):

    def test_recall_at_k(self):
        score = recall_at_k(
            retrieved_ids=[10, 20, 30, 40],
            relevant_ids={20, 40},
            k=3,
        )

        self.assertEqual(score, 0.5)

    def test_recall_at_k_with_all_relevant(self):
        score = recall_at_k(
            retrieved_ids=[10, 20, 30],
            relevant_ids={10, 20},
            k=2,
        )

        self.assertEqual(score, 1.0)

    def test_reciprocal_rank(self):
        score = reciprocal_rank(
            retrieved_ids=[10, 20, 30],
            relevant_ids={30},
        )

        self.assertAlmostEqual(score, 1 / 3)

    def test_reciprocal_rank_with_no_match(self):
        score = reciprocal_rank(
            retrieved_ids=[10, 20],
            relevant_ids={30},
        )

        self.assertEqual(score, 0.0)

    def test_mean_reciprocal_rank(self):
        score = mean_reciprocal_rank(
            rankings=[
                [10, 20],
                [30, 40],
            ],
            relevant_sets=[
                {10},
                {40},
            ],
        )

        self.assertEqual(score, 0.75)

    def test_rejects_invalid_k(self):
        with self.assertRaises(ValueError):
            recall_at_k([10], {10}, 0)

    def test_rejects_empty_relevant_set(self):
        with self.assertRaises(ValueError):
            recall_at_k([10], set(), 1)

    def test_rejects_mismatched_lengths(self):
        with self.assertRaises(ValueError):
            mean_reciprocal_rank(
                rankings=[[10]],
                relevant_sets=[{10}, {20}],
            )

    def test_hit_at_k_finds_relevant_chunk(self):
        retrieved = [10, 20, 30]
        relevant = {20, 40}

        self.assertEqual(hit_at_k(retrieved, relevant, 1), 0.0)
        self.assertEqual(hit_at_k(retrieved, relevant, 2), 1.0)
        self.assertEqual(hit_at_k(retrieved, relevant, 3), 1.0)


    def test_hit_at_k_rejects_invalid_inputs(self):
        with self.assertRaises(ValueError):
            hit_at_k([10], {10}, 0)

        with self.assertRaises(ValueError):
            hit_at_k([10], set(), 5)