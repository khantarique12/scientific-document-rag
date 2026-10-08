from unittest.mock import Mock

import requests
from django.test import SimpleTestCase

from documents.services.ollama_client import OllamaClient, OllamaError


class OllamaClientTests(SimpleTestCase):

    def setUp(self):
        self.session = Mock()
        self.response = Mock()
        self.response.json.return_value = {
            "response": "RDF represents information using triples."
        }
        self.session.post.return_value = self.response

        self.client = OllamaClient(
            base_url="http://localhost:11434",
            model="qwen3:1.7b",
            session=self.session,
        )

    def test_generate_returns_answer(self):
        answer = self.client.generate("What is RDF?")

        self.assertEqual(
            answer,
            "RDF represents information using triples.",
        )

    def test_generate_sends_correct_request(self):
        self.client.generate("What is RDF?")

        self.session.post.assert_called_once_with(
            "http://localhost:11434/api/generate",
            json={
                "model": "qwen3:1.7b",
                "prompt": "What is RDF?",
                "stream": False,
                "think": False,
                "options": {
                    "num_predict": 512,
                },
            },
            timeout=120,
        )

    def test_generate_rejects_empty_prompt(self):
        with self.assertRaises(ValueError):
            self.client.generate("   ")

        self.session.post.assert_not_called()

    def test_generate_handles_connection_error(self):
        self.session.post.side_effect = requests.ConnectionError(
            "Connection refused"
        )

        with self.assertRaises(OllamaError):
            self.client.generate("What is RDF?")

    def test_generate_handles_http_error(self):
        self.response.raise_for_status.side_effect = (
            requests.HTTPError("Server error")
        )

        with self.assertRaises(OllamaError):
            self.client.generate("What is RDF?")

    def test_generate_handles_invalid_json(self):
        self.response.json.side_effect = ValueError("Invalid JSON")

        with self.assertRaises(OllamaError):
            self.client.generate("What is RDF?")

    def test_generate_rejects_empty_response(self):
        self.response.json.return_value = {"response": "  "}

        with self.assertRaises(OllamaError):
            self.client.generate("What is RDF?")

    def test_generate_rejects_missing_response(self):
        self.response.json.return_value = {}

        with self.assertRaises(OllamaError):
            self.client.generate("What is RDF?")