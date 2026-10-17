
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APITestCase

from documents.models import Document
from documents.services.ollama_client import OllamaError


class QuestionAnswerAPITests(APITestCase):

    URL = "/api/documents/ask/"

    @patch("documents.api.views.RAGService")
    def test_returns_answer_and_citations(self, mock_rag_service):
        expected_result = {
            "question": "What is RDF?",
            "answer": "RDF represents data as triples [Source 1].",
            "sources": [
                {
                    "source_id": 1,
                    "document_id": 1,
                    "document_title": "Scientific Paper",
                    "page_number": 12,
                    "chunk_id": 5,
                    "similarity": 0.85,
                }
            ],
            "citations": [
                {
                    "source_id": 1,
                    "document_id": 1,
                    "document_title": "Scientific Paper",
                    "page_number": 12,
                    "chunk_id": 5,
                    "similarity": 0.85,
                }
            ],
        }

        mock_rag_service.return_value.ask.return_value = expected_result

        response = self.client.post(
            self.URL,
            {
                "question": "What is RDF?",
                "limit": 3,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected_result)

        mock_rag_service.return_value.ask.assert_called_once_with(
            question="What is RDF?",
            limit=3,
            document_id=None,
        )

    @patch("documents.api.views.RAGService")
    def test_rejects_empty_question(self, mock_rag_service):
        response = self.client.post(
            self.URL,
            {"question": ""},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        mock_rag_service.assert_not_called()

    @patch("documents.api.views.RAGService")
    def test_rejects_invalid_limit(self, mock_rag_service):
        response = self.client.post(
            self.URL,
            {
                "question": "What is RDF?",
                "limit": 0,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        mock_rag_service.assert_not_called()

    @patch("documents.api.views.RAGService")
    def test_uses_default_limit(self, mock_rag_service):
        mock_rag_service.return_value.ask.return_value = {
            "question": "What is RDF?",
            "answer": "No relevant information found.",
            "sources": [],
            "citations": [],
        }

        response = self.client.post(
            self.URL,
            {"question": "What is RDF?"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        mock_rag_service.return_value.ask.assert_called_once_with(
            question="What is RDF?",
            limit=5,
            document_id=None,
        )

    @patch("documents.api.views.RAGService")
    def test_returns_503_when_ollama_fails(self, mock_rag_service):
        mock_rag_service.return_value.ask.side_effect = OllamaError(
            "Connection failed."
        )

        response = self.client.post(
            self.URL,
            {"question": "What is RDF?"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_503_SERVICE_UNAVAILABLE,
        )
        self.assertIn("detail", response.data)

    @patch("documents.api.views.RAGService")
    def test_filters_by_selected_document(self, mock_rag_service):
        document = Document.objects.create(
            title="Selected Scientific Paper",
            original_filename="selected.pdf",
            status="ready",
        )

        mock_rag_service.return_value.ask.return_value = {
            "question": "What is RDF?",
            "answer": "RDF represents data as triples.",
            "sources": [],
            "citations": [],
        }

        response = self.client.post(
            self.URL,
            {
                "question": "What is RDF?",
                "limit": 3,
                "document_id": document.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        mock_rag_service.return_value.ask.assert_called_once_with(
            question="What is RDF?",
            limit=3,
            document_id=document.id,
        )

    @patch("documents.api.views.RAGService")
    def test_rejects_nonexistent_document(self, mock_rag_service):
        response = self.client.post(
            self.URL,
            {
                "question": "What is RDF?",
                "document_id": 999999,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        mock_rag_service.assert_not_called()

    @patch("documents.api.views.RAGService")
    def test_rejects_unprocessed_document(self, mock_rag_service):
        document = Document.objects.create(
            title="Unprocessed Paper",
            original_filename="unprocessed.pdf",
            status="uploaded",
        )

        response = self.client.post(
            self.URL,
            {
                "question": "What is RDF?",
                "document_id": document.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        mock_rag_service.assert_not_called()
