export type DocumentStatus =
  | "uploaded"
  | "processing"
  | "ready"
  | "failed"

export interface Document {
  id: number
  title: string
  original_filename: string
  file: string
  page_count: number
  status: DocumentStatus
  created_at: string
  updated_at: string
}
