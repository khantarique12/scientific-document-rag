from unittest.mock import Mock

import numpy as np
from django.test import SimpleTestCase

from documents.services.embedding import EmbeddingService


class EmbeddingServiceTests(SimpleTestCase):
    def test_embed_returns_list(self):
        model = Mock()
        model.encode.return_value = np.array(
            [0.1, 0.2, 0.3],
            dtype=np.float32,
        )

        service = EmbeddingService(model=model)

        embedding = service.embed("Scientific document")

        self.assertIsInstance(embedding, list)
        self.assertEqual(len(embedding), 3)

    def test_embed_calls_model_with_normalization(self):
        model = Mock()
        model.encode.return_value = np.array(
            [0.1, 0.2],
            dtype=np.float32,
        )

        service = EmbeddingService(model=model)

        service.embed("KPI semantic representation")

        model.encode.assert_called_once_with(
            "KPI semantic representation",
            normalize_embeddings=True,
        )

    def test_empty_text_raises_error(self):
        model = Mock()
        service = EmbeddingService(model=model)

        with self.assertRaises(ValueError):
            service.embed("")

        model.encode.assert_not_called()

    def test_whitespace_only_text_raises_error(self):
        model = Mock()
        service = EmbeddingService(model=model)

        with self.assertRaises(ValueError):
            service.embed("   ")

        model.encode.assert_not_called()

    def test_embed_batch_returns_embeddings(self):
        model = Mock()
        model.encode.return_value = np.array(
            [
                [0.1, 0.2],
                [0.3, 0.4],
            ],
            dtype=np.float32,
        )

        service = EmbeddingService(model=model)

        embeddings = service.embed_batch(
            [
                "First scientific chunk",
                "Second scientific chunk",
            ]
        )

        self.assertIsInstance(embeddings, list)
        self.assertEqual(len(embeddings), 2)
        self.assertEqual(len(embeddings[0]), 2)

        model.encode.assert_called_once_with(
            [
                "First scientific chunk",
                "Second scientific chunk",
            ],
            normalize_embeddings=True,
        )

    def test_embed_batch_with_empty_list_returns_empty_list(self):
        model = Mock()
        service = EmbeddingService(model=model)

        embeddings = service.embed_batch([])

        self.assertEqual(embeddings, [])
        model.encode.assert_not_called()

    def test_embed_batch_rejects_empty_text(self):
        model = Mock()
        service = EmbeddingService(model=model)

        with self.assertRaises(ValueError):
            service.embed_batch(
                [
                    "Valid chunk",
                    "   ",
                ]
            )

        model.encode.assert_not_called()