"""Orchestrate retrieval-augmented question answering."""

from documents.services.ollama_client import OllamaClient
from documents.services.prompt_builder import PromptBuilder
from documents.services.retrieval import RetrievalService
from documents.services.citations import CitationService

class RAGService:
    """Generate answers grounded in retrieved document passages."""

    def __init__(
        self,
        retrieval_service=None,
        llm_client=None,
        prompt_builder=None,
    ):
        self.retrieval_service = (
            retrieval_service
            if retrieval_service is not None
            else RetrievalService()
        )
        self.llm_client = (
            llm_client
            if llm_client is not None
            else OllamaClient()
        )
        self.prompt_builder = (
            prompt_builder
            if prompt_builder is not None
            else PromptBuilder()
        )

    def ask(self, question: str, limit: int = 5) -> dict:
        """Retrieve evidence and generate an answer."""

        if not question.strip():
            raise ValueError("Question cannot be empty.")

        if limit <= 0:
            raise ValueError("Limit must be greater than zero.")

        chunks = self.retrieval_service.search(
            question,
            limit=limit,
        )

        if not chunks:
            return {
                "question": question,
                "answer": (
                    "The answer cannot be determined from "
                    "the provided documents."
                ),
                "sources": [],
                "citations": [],
            }

        prompt = self.prompt_builder.build(question, chunks)
        answer = self.llm_client.generate(prompt)

        sources = []

        for index, chunk in enumerate(chunks, start=1):
            sources.append({
                "source_id": index,
                "document_id": chunk.page.document.id,
                "document_title": chunk.page.document.title,
                "page_number": chunk.page.page_number,
                "chunk_id": chunk.id,
                "similarity": round(1 - chunk.distance, 4),
            })

        citations = CitationService.extract(answer, sources)

        return {
            "question": question,
            "answer": answer,
            "sources": sources,
            "citations": citations,
        }