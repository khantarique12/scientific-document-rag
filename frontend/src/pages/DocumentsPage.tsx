
import { useEffect, useState } from "react"
import { FileText, RefreshCw } from "lucide-react"

import { getDocuments } from "@/api/documents"
import type { Document, DocumentStatus } from "@/types/document"
import { UploadDocument } from "@/components/documents/UploadDocument"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

const statusVariants: Record<
  DocumentStatus,
  "default" | "secondary" | "destructive" | "outline"
> = {
  ready: "default",
  uploaded: "secondary",
  processing: "outline",
  failed: "destructive",
}

export function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function loadDocuments(signal?: AbortSignal) {
    setLoading(true)
    setError(null)

    try {
      const data = await getDocuments(signal)

      if (!signal?.aborted) {
        setDocuments(data)
      }
    } catch (err) {
      if (!signal?.aborted) {
        setError(
          err instanceof Error
            ? err.message
            : "Unable to load documents",
        )
      }
    } finally {
      if (!signal?.aborted) {
        setLoading(false)
      }
    }
  }

  useEffect(() => {
    const controller = new AbortController()

    void loadDocuments(controller.signal)

    return () => controller.abort()
  }, [])

  return (
    <div className="mx-auto max-w-6xl space-y-6">

      {/* Page heading */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            Documents
          </h1>

          <p className="mt-1 text-sm text-muted-foreground">
            Browse, upload, and manage your research documents.
          </p>
        </div>

        <Button
          variant="outline"
          disabled={loading}
          onClick={() => void loadDocuments()}
        >
          <RefreshCw className="size-4" />
          Refresh
        </Button>
      </div>

      {/* PDF upload */}
      <UploadDocument
        onUploaded={() => void loadDocuments()}
      />

      {/* Loading */}
      {loading && (
        <p
          role="status"
          className="text-sm text-muted-foreground"
        >
          Loading documents...
        </p>
      )}

      {/* Error */}
      {error && (
        <Card>
          <CardContent className="space-y-3 pt-6">
            <p
              role="alert"
              className="text-sm text-destructive"
            >
              {error}
            </p>

            <Button
              variant="outline"
              onClick={() => void loadDocuments()}
            >
              Try again
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Empty state */}
      {!loading && !error && documents.length === 0 && (
        <Card>
          <CardContent className="py-12 text-center">
            <FileText className="mx-auto mb-3 size-8 text-muted-foreground" />

            <p className="font-medium">
              No documents yet
            </p>

            <p className="mt-1 text-sm text-muted-foreground">
              Upload a PDF to start building your research library.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Document list */}
      {!loading && !error && documents.length > 0 && (
        <div className="space-y-4">

          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">
              Your Documents
            </h2>

            <span className="text-sm text-muted-foreground">
              {documents.length} documents
            </span>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            {documents.map((document) => (
              <Card key={document.id}>
                <CardHeader>
                  <div className="flex items-start justify-between gap-3">

                    <div className="flex min-w-0 items-center gap-3">
                      <FileText className="size-5 shrink-0 text-muted-foreground" />

                      <CardTitle className="truncate text-base">
                        {document.title}
                      </CardTitle>
                    </div>

                    <Badge
                      variant={statusVariants[document.status]}
                    >
                      {document.status}
                    </Badge>
                  </div>
                </CardHeader>

                <CardContent className="space-y-3">

                  <p className="truncate text-sm text-muted-foreground">
                    {document.original_filename}
                  </p>

                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">
                      {document.page_count} pages
                    </span>

                    <span className="text-muted-foreground">
                      {new Date(
                        document.created_at,
                      ).toLocaleDateString()}
                    </span>
                  </div>

                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
