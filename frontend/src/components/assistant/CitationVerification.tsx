
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

  const groupedResults = new Map<
    number,
    CitationVerificationResult[]
  >()

  for (const result of results) {
    const group = groupedResults.get(result.source_id) ?? []
    group.push(result)
    groupedResults.set(result.source_id, group)
  }

  return (
    <section className="space-y-3 border-t pt-4">
      <h3 className="text-sm font-semibold">
        Citation verification
      </h3>

      <p className="text-xs text-muted-foreground">
        Automated evidence checks are estimates, not proof of accuracy.
      </p>

      {Array.from(groupedResults.entries()).map(
        ([sourceId, claims]) => {
          const citedSource = sourceMap.get(sourceId)

          const supportedCount = claims.filter(
            (claim) => claim.supported,
          ).length

          const allSupported =
            supportedCount === claims.length

          return (
            <div
              key={sourceId}
              className="space-y-3 rounded-lg border p-4"
            >
              <div className="flex items-center gap-2">
                {allSupported ? (
                  <CheckCircle2 className="size-4 text-green-600" />
                ) : (
                  <AlertTriangle className="size-4 text-amber-600" />
                )}

                <span className="text-sm font-medium">
                  {allSupported
                    ? "Citation appears supported"
                    : "Citation needs review"}
                </span>
              </div>

              <p className="text-sm text-muted-foreground">
                {supportedCount} of {claims.length} claims supported
                {" · "}
                Source {sourceId}
                {citedSource &&
                  ` · Page ${citedSource.page_number}`}
              </p>

              {citedSource && (
                <Link
                  to={`/documents/${citedSource.document_id}?page=${citedSource.page_number}`}
                  className="inline-flex items-center gap-1 text-xs font-medium underline-offset-4 hover:underline"
                >
                  <BookOpen className="size-3" />
                  Open cited passage
                </Link>
              )}

              <details className="border-t pt-3">
                <summary className="cursor-pointer text-xs font-medium">
                  View individual claims
                </summary>

                <div className="mt-3 space-y-3">
                  {claims.map((claim, index) => (
                    <div
                      key={index}
                      className="rounded-md border p-3 text-xs"
                    >
                      <div className="mb-2 flex items-center gap-2">
                        {claim.supported ? (
                          <CheckCircle2 className="size-3 text-green-600" />
                        ) : (
                          <AlertTriangle className="size-3 text-amber-600" />
                        )}

                        <span className="font-medium">
                          {claim.label}
                        </span>
                      </div>

                      <p className="leading-5">
                        {claim.claim}
                      </p>

                      {!claim.supported &&
                        claim.alternative_sources.length > 0 && (
                          <div className="mt-3 space-y-2 border-t pt-3">
                            <p className="font-medium">
                              Suggested evidence to review
                            </p>

                            {claim.alternative_sources.map(
                              (alternative) => (
                                <Link
                                  key={`${alternative.source_id}-${alternative.chunk_id}`}
                                  to={`/documents/${alternative.document_id}?page=${alternative.page_number}`}
                                  className="block rounded border p-2 hover:bg-accent"
                                >
                                  Source {alternative.source_id}
                                  {" · "}
                                  Page {alternative.page_number}
                                  {" · "}
                                  Chunk {alternative.chunk_id}
                                </Link>
                              ),
                            )}
                          </div>
                        )}
                    </div>
                  ))}
                </div>
              </details>
            </div>
          )
        },
      )}
    </section>
  )
}
