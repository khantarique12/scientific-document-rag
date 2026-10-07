from rest_framework import generics
from rest_framework.parsers import FormParser, MultiPartParser

from documents.models import Document

from .serializers import DocumentSerializer


class DocumentListCreateView(generics.ListCreateAPIView):
    queryset = Document.objects.all().order_by("-created_at")
    serializer_class = DocumentSerializer
    parser_classes = [MultiPartParser, FormParser]