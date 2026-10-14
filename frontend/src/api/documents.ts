import type { Document } from "@/types/document"

const API_BASE = "/api/documents/"

// Fetch all documents
export async function getDocuments(
  signal?: AbortSignal,
): Promise<Document[]> {
  const response = await fetch(API_BASE, { signal })

  if (!response.ok) {
    throw new Error(
      `Failed to load documents (HTTP ${response.status})`,
    )
  }

  return (await response.json()) as Document[]
}

// Upload a PDF document
export async function uploadDocument(
  file: File,
  title: string,
): Promise<Document> {
  const formData = new FormData()

  formData.append("title", title)
  formData.append("file", file)

  const response = await fetch(API_BASE, {
    method: "POST",
    body: formData,
  })

  const data: unknown = await response.json()

  if (!response.ok) {
    throw new Error(
      typeof data === "object" &&
      data !== null &&
      "file" in data &&
      Array.isArray(data.file)
        ? String(data.file[0])
        : `Upload failed (HTTP ${response.status})`,
    )
  }

  return data as Document
}

// Fetch one document by ID
export async function getDocument(
  id: number,
  signal?: AbortSignal,
): Promise<Document> {
  const response = await fetch(`${API_BASE}${id}/`, { signal })

  if (!response.ok) {
    throw new Error(
      `Failed to load document (HTTP ${response.status})`,
    )
  }

  return (await response.json()) as Document
}