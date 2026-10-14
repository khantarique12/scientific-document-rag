import { useEffect, useState } from "react"
import { Link, useParams, useSearchParams } from "react-router"
import { ArrowLeft, ExternalLink } from "lucide-react"

import { getDocument } from "@/api/documents"
import { PDFViewer } from "@/components/pdf/PDFViewer"
import { Badge } from "@/components/ui/badge"
import type { Document } from "@/types/document"

export function DocumentDetailPage() {
  const { id } = useParams()
  const [searchParams] = useSearchParams()

  const [document, setDocument] = useState<Document | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const documentId = Number(id)

  // Support URLs such as /documents/2?page=5
  const requestedPage = Number(searchParams.get("page") || "1")

  const initialPage =
    Number.isInteger(requestedPage) && requestedPage > 0
      ? requestedPage
      : 1

  useEffect(() => {
    if (!Number.isInteger(documentId) || documentId <= 0) {
      return
    }

    const controller = new AbortController()

    setLoading(true)
    setError(null)
    setDocument(null)

    getDocument(documentId, controller.signal)
      .then((data) => {
        if (!controller.signal.aborted) {
          setDocument(data)
        }
      })
      .catch((error: unknown) => {
        if (!controller.signal.aborted) {
          setError(
            error instanceof Error
              ? error.message
              : "Unable to load document",
          )
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setLoading(false)
        }
      })

    return () => controller.abort()
  }, [documentId])

  // Invalid document ID
  if (!Number.isInteger(documentId) || documentId <= 0) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-semibold">
          Invalid document
        </h1>

        <p className="text-sm text-muted-foreground">
          The document ID is invalid.
        </p>

        <Link
          to="/documents"
          className="inline-flex items-center gap-2 text-sm font-medium hover:underline"
        >
          <ArrowLeft className="size-4" />
          Back to Documents
        </Link>
      </div>
    )
  }

  // Loading state
  if (loading) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-semibold">
          Loading document...
        </h1>

        <p className="text-sm text-muted-foreground">
          Please wait while we retrieve the document.
        </p>
      </div>
    )
  }

  // Error state
  if (error || !document) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-semibold">
          Unable to load document
        </h1>

        <p className="text-sm text-destructive">
          {error || "Document not found"}
        </p>

        <Link
          to="/documents"
          className="inline-flex items-center gap-2 text-sm font-medium hover:underline"
        >
          <ArrowLeft className="size-4" />
          Back to Documents
        </Link>
      </div>
    )
  }

  // Use the Vite /media proxy instead of Django's absolute URL.
  const pdfUrl = new URL(document.file, window.location.origin)
  const fileUrl = `${pdfUrl.pathname}${pdfUrl.search}`

  return (
    <div className="space-y-6">

      {/* Back navigation */}
      <Link
        to="/documents"
        className="inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors hover:bg-accent"
      >
        <ArrowLeft className="size-4" />
        Back to Documents
      </Link>

      {/* Document header */}
      <div className="flex flex-wrap items-start justify-between gap-4">

        <div className="min-w-0 space-y-2">
          <h1 className="text-2xl font-semibold">
            {document.title}
          </h1>

          <p className="break-all text-sm text-muted-foreground">
            {document.original_filename}
          </p>

          <p className="text-sm text-muted-foreground">
            {document.page_count} pages
            {" · "}
            Uploaded{" "}
            {new Date(document.created_at).toLocaleDateString()}
          </p>
        </div>

        {/* Status and PDF link */}
        <div className="flex flex-wrap items-center gap-3">

          <Badge variant="secondary">
            {document.status}
          </Badge>

          <a
            href={fileUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-md border bg-background px-3 py-2 text-sm font-medium transition-colors hover:bg-accent"
          >
            <ExternalLink className="size-4" />
            Open PDF
          </a>

        </div>
      </div>

      {/* PDF viewer */}
      <PDFViewer
        key={`${document.id}-${initialPage}`}
        fileUrl={fileUrl}
        initialPage={initialPage}
      />

    </div>
  )
}