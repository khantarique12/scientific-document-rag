"""Tests for cross-encoder reranking."""

from types import SimpleNamespace
from unittest.mock import Mock

from django.test import SimpleTestCase

from documents.services.reranking import RerankingService


class RerankingServiceTests(SimpleTestCase):

    def setUp(self):
        self.first = SimpleNamespace(id=1, text="General KPI information.")
        self.second = SimpleNamespace(id=2, text="SMART criteria for KPIs.")
        self.third = SimpleNamespace(id=3, text="Unrelated information.")

        self.model = Mock()
        self.model.predict.return_value = [0.5, 8.2, -0.7]

        self.service = RerankingService(model=self.model)

    def test_returns_chunks_in_ranked_order(self):
        result = self.service.rerank(
            "What are SMART criteria?",
            [self.first, self.second, self.third],
        )

        self.assertEqual(
            result,
            [self.second, self.first, self.third],
        )

    def test_optionally_returns_scores(self):
        result = self.service.rerank(
            "What are SMART criteria?",
            [self.first, self.second, self.third],
            return_scores=True,
        )

        self.assertEqual(
            result,
            [
                (self.second, 8.2),
                (self.first, 0.5),
                (self.third, -0.7),
            ],
        )

    def test_respects_limit(self):
        result = self.service.rerank(
            "What are SMART criteria?",
            [self.first, self.second, self.third],
            limit=1,
        )

        self.assertEqual(result, [self.second])

    def test_handles_empty_chunks(self):
        result = self.service.rerank("What are SMART criteria?", [])

        self.assertEqual(result, [])
        self.model.predict.assert_not_called()

    def test_rejects_empty_query(self):
        with self.assertRaises(ValueError):
            self.service.rerank(" ", [self.first])

    def test_rejects_invalid_limit(self):
        with self.assertRaises(ValueError):
            self.service.rerank("What are SMART criteria?", [self.first], limit=0)