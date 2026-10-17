
"""Orchestrate retrieval-augmented question answering."""

from documents.services.ollama_client import OllamaClient
from documents.services.prompt_builder import PromptBuilder
from documents.services.retrieval import RetrievalService
from documents.services.reranking import RerankingService
from documents.services.citations import CitationService
from documents.services.context_selection import ContextSelectionService


class RAGService:
    """Generate answers grounded in retrieved document passages."""

    CANDIDATE_LIMIT = 30

    def __init__(
        self,
        retrieval_service=None,
        llm_client=None,
        prompt_builder=None,
        reranking_service=None,
        use_reranking=True,
        context_selection_service=None,
        use_context_selection=True,
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

        self.use_reranking = use_reranking
        self.reranking_service = reranking_service

        self.use_context_selection = use_context_selection
        self.context_selection_service = (
            context_selection_service
            if context_selection_service is not None
            else ContextSelectionService()
        )

    def ask(
        self,
        question: str,
        limit: int = 5,
        document_id: int | None = None,
    ) -> dict:
        """Retrieve, rerank, select evidence, and generate an answer."""

        if not question.strip():
            raise ValueError("Question cannot be empty.")

        if limit <= 0:
            raise ValueError("Limit must be greater than zero.")

        # Step 1: Retrieve candidate passages.
        candidate_limit = (
            max(limit, self.CANDIDATE_LIMIT)
            if self.use_reranking
            else (
                max(limit * 2, 10)
                if self.use_context_selection
                else limit
            )
        )

        chunks = self.retrieval_service.search(
            question,
            limit=candidate_limit,
            document_id=document_id,
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

        # Step 2: Rerank candidates by relevance.
        if self.use_reranking:
            if self.reranking_service is None:
                self.reranking_service = RerankingService()

            rerank_limit = (
                max(limit * 2, 10)
                if self.use_context_selection
                else limit
            )

            chunks = self.reranking_service.rerank(
                question,
                chunks,
                limit=rerank_limit,
            )

        # Step 3: Remove substantially overlapping passages.
        if self.use_context_selection:
            chunks = self.context_selection_service.select(
                chunks,
                limit=limit,
            )
        else:
            chunks = chunks[:limit]

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

        # Step 4: Build an evidence-grounded prompt.
        prompt = self.prompt_builder.build(
            question,
            chunks,
        )

        # Step 5: Generate an answer using Ollama.
        answer = self.llm_client.generate(prompt).strip()

        insufficient_evidence = (
            "The answer cannot be determined from "
            "the provided documents."
        )

        if (
            insufficient_evidence in answer
            and answer != insufficient_evidence
        ):
            answer = answer.replace(
                insufficient_evidence,
                "",
            ).strip()

        if not answer:
            answer = insufficient_evidence

        # Step 6: Prepare source metadata.
        sources = []

        for index, chunk in enumerate(chunks, start=1):
            sources.append({
                "source_id": index,
                "document_id": chunk.page.document.id,
                "document_title": chunk.page.document.title,
                "page_number": chunk.page.page_number,
                "chunk_id": chunk.id,
                "similarity": (
                    round(1 - chunk.distance, 4)
                    if chunk.distance is not None
                    else None
                ),
                "text": chunk.text,
            })

        # Step 7: Extract citations from the generated answer.
        citations = CitationService.extract(
            answer,
            sources,
        )

        return {
            "question": question,
            "answer": answer,
            "sources": sources,
            "citations": citations,
        }
