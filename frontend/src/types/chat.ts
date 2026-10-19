
export interface RAGSource {
  source_id: number
  document_id: number
  document_title: string
  page_number: number
  chunk_id: number
  similarity: number
  text: string
}

export interface AlternativeSource {
  source_id: number
  document_id: number
  page_number: number
  chunk_id: number
  entailment_score: number
}

export interface CitationVerification {
  claim: string
  source_id: number
  supported: boolean
  label: string
  confidence: number | null
  alternative_sources: AlternativeSource[]
}

export interface RAGResponse {
  question: string
  answer: string
  sources: RAGSource[]
  citations: RAGSource[]
  citation_verification?: CitationVerification[]
}
