
from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from documents.models import Document
from documents.services.ollama_client import OllamaError
from documents.services.rag import RAGService

from .serializers import DocumentSerializer, QuestionSerializer


class DocumentListCreateView(generics.ListCreateAPIView):
    queryset = Document.objects.all().order_by("-created_at")
    serializer_class = DocumentSerializer
    parser_classes = [MultiPartParser, FormParser]


class QuestionAnswerView(APIView):
    """Answer questions using indexed scientific documents."""

    def post(self, request):
        serializer = QuestionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        question = serializer.validated_data["question"]
        limit = serializer.validated_data["limit"]

        try:
            result = RAGService().ask(
                question=question,
                limit=limit,
            )
        except OllamaError:
            return Response(
                {
                    "detail": (
                        "The language model is currently unavailable."
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(result, status=status.HTTP_200_OK)
