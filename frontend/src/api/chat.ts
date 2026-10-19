
import type { RAGResponse } from "@/types/chat"

const ASK_ENDPOINT = "/api/documents/ask/"

export async function askQuestion(
  question: string,
  limit = 5,
  documentId?: number,
  verifyCitations = true,
): Promise<RAGResponse> {
  const response = await fetch(ASK_ENDPOINT, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      question,
      limit,
      verify_citations: verifyCitations,
      ...(documentId !== undefined
        ? { document_id: documentId }
        : {}),
    }),
  })

  if (!response.ok) {
    throw new Error(
      `Unable to generate answer (HTTP ${response.status})`,
    )
  }

  return (await response.json()) as RAGResponse
}
