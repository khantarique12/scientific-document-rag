export interface RAGSource {
  source_id: number
  document_id: number
  document_title: string
  page_number: number
  chunk_id: number
  similarity: number
  text: string
}

export interface RAGResponse {
  question: string
  answer: string
  sources: RAGSource[]
  citations: RAGSource[]
}