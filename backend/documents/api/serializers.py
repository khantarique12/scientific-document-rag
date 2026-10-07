from pathlib import Path

from rest_framework import serializers
from documents.services.document_processor import DocumentProcessingService
from documents.services.pdf_extractor import PDFExtractionError
from documents.models import Document


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            "id",
            "title",
            "original_filename",
            "file",
            "page_count",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "original_filename",
            "page_count",
            "status",
            "created_at",
            "updated_at",
        ]

    def validate_file(self, uploaded_file):
        if Path(uploaded_file.name).suffix.lower() != ".pdf":
            raise serializers.ValidationError("Only PDF files are supported.")

        return uploaded_file

    def create(self, validated_data):
        uploaded_file = validated_data["file"]

        document = Document.objects.create(
            original_filename=uploaded_file.name,
            **validated_data,
        )

        try:
            DocumentProcessingService().process(document)
        except PDFExtractionError:
            pass

        return document
