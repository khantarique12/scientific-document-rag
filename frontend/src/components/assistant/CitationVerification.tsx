
import { Link } from "react-router"
import { AlertTriangle, BookOpen, CheckCircle2 } from "lucide-react"

import type {
  CitationVerification as CitationVerificationResult,
  RAGSource,
} from "@/types/chat"

interface Props {
  results?: CitationVerificationResult[]
  sources: RAGSource[]
}

export function CitationVerification({ results, sources }: Props) {
  if (!results || results.length === 0) {
    return null
  }

  const sourceMap = new Map(
    sources.map((source) => [source.source_id, source]),
  )

  return (
    <section className="space-y-3 border-t pt-4">
      <h3 className="text-sm font-semibold">
        Citation verification
      </h3>

      <p className="text-xs text-muted-foreground">
        Automated evidence checks are estimates, not proof of accuracy.
      </p>

      {results.map((result, index) => {
        const citedSource = sourceMap.get(result.source_id)

        return (
          <div
            key={`${result.source_id}-${index}`}
            className="space-y-3 rounded-lg border p-4"
          >
            <div className="flex items-center gap-2">
              {result.supported ? (
                <>
                  <CheckCircle2 className="size-4 text-green-600" />
                  <span className="text-sm font-medium">
                    Evidence appears to support this citation
                  </span>
                </>
              ) : (
                <>
                  <AlertTriangle className="size-4 text-amber-600" />
                  <span className="text-sm font-medium">
                    Citation needs review
                  </span>
                </>
              )}
            </div>

            <p className="text-sm leading-6">
              {result.claim}
            </p>

            <div className="text-xs text-muted-foreground">
              Cited source: {result.source_id}
              {citedSource && (
                <>
                  {" · "}
                  Page {citedSource.page_number}
                </>
              )}
              {" · "}
              Model label: {result.label}
            </div>

            {citedSource && (
              <Link
                to={`/documents/${citedSource.document_id}?page=${citedSource.page_number}`}
                className="inline-flex items-center gap-1 text-xs font-medium underline-offset-4 hover:underline"
              >
                <BookOpen className="size-3" />
                Open cited passage
              </Link>
            )}

            {!result.supported &&
              result.alternative_sources.length > 0 && (
                <div className="space-y-2 border-t pt-3">
                  <p className="text-xs font-semibold">
                    Suggested evidence to review
                  </p>

                  {result.alternative_sources.map((alternative) => (
                    <Link
                      key={`${alternative.source_id}-${alternative.chunk_id}`}
                      to={`/documents/${alternative.document_id}?page=${alternative.page_number}`}
                      className="flex items-center justify-between gap-3 rounded-md border p-3 text-xs hover:bg-accent"
                    >
                      <span>
                        Source {alternative.source_id}
                        {" · "}
                        Page {alternative.page_number}
                        {" · "}
                        Chunk {alternative.chunk_id}
                      </span>

                      <span className="text-muted-foreground">
                        Candidate
                      </span>
                    </Link>
                  ))}
                </div>
              )}
          </div>
        )
      })}
    </section>
  )
}
