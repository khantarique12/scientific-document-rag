
import { useEffect, useState, type FormEvent } from "react"
import { Link } from "react-router"
import {
  ArrowUp,
  BookOpen,
  ExternalLink,
  Loader2,
  MessageSquare,
  Sparkles,
} from "lucide-react"

import { askQuestion } from "@/api/chat"
import { getDocuments } from "@/api/documents"
import type { Document } from "@/types/document"
import type { RAGResponse, RAGSource } from "@/types/chat"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { CitationVerification } from "@/components/assistant/CitationVerification"

interface ChatMessage {
  id: number
  question: string
  scopeLabel: string
  result: RAGResponse
}

function CitationLink({ source }: { source: RAGSource }) {
  return (
    <Link
      to={`/documents/${source.document_id}?page=${source.page_number}`}
      className="inline-flex items-center gap-1 rounded-md border px-2 py-1 text-xs font-medium hover:bg-accent"
    >
      <BookOpen className="size-3" />
      Source {source.source_id}
      <ExternalLink className="size-3" />
    </Link>
  )
}

function AnswerText({
  answer,
  sources,
}: {
  answer: string
  sources: RAGSource[]
}) {
  const sourceMap = new Map(
    sources.map((source) => [source.source_id, source]),
  )

  const parts = answer.split(/(\[Source \d+\])/g)

  return (
    <div className="whitespace-pre-wrap text-sm leading-7">
      {parts.map((part, index) => {
        const match = part.match(/^\[Source (\d+)\]$/)

        if (match) {
          const source = sourceMap.get(Number(match[1]))

          if (source) {
            return (
              <span key={index} className="mx-1 inline-block">
                <CitationLink source={source} />
              </span>
            )
          }
        }

        return <span key={index}>{part}</span>
      })}
    </div>
  )
}

export function AssistantPage() {
  const [question, setQuestion] = useState("")
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [documents, setDocuments] = useState<Document[]>([])
  const [selectedDocumentId, setSelectedDocumentId] = useState("")
  const [documentsLoading, setDocumentsLoading] = useState(true)
  const [documentsError, setDocumentsError] = useState<string | null>(
    null,
  )

  useEffect(() => {
    const controller = new AbortController()

    async function loadDocuments() {
      try {
        const data = await getDocuments(controller.signal)
        setDocuments(
          data.filter((document) => document.status === "ready"),
        )
        setDocumentsError(null)
      } catch (error: unknown) {
        if (controller.signal.aborted) return

        setDocumentsError(
          error instanceof Error
            ? error.message
            : "Unable to load documents.",
        )
      } finally {
        if (!controller.signal.aborted) {
          setDocumentsLoading(false)
        }
      }
    }

    void loadDocuments()

    return () => controller.abort()
  }, [])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    const trimmedQuestion = question.trim()

    if (
      !trimmedQuestion ||
      loading ||
      documentsLoading ||
      documentsError
    ) {
      return
    }

    const selectedDocument = documents.find(
      (document) => String(document.id) === selectedDocumentId,
    )

    const documentId = selectedDocument?.id
    const scopeLabel = selectedDocument
      ? selectedDocument.title
      : "All documents"

    setLoading(true)
    setError(null)

    try {
      const result = await askQuestion(
        trimmedQuestion,
        5,
        documentId,
      )

      setMessages((previous) => [
        ...previous,
        {
          id: Date.now(),
          question: trimmedQuestion,
          scopeLabel,
          result,
        },
      ])

      setQuestion("")
    } catch (error: unknown) {
      setError(
        error instanceof Error
          ? error.message
          : "Unable to generate an answer.",
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-6">
      {/* Header */}
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <Sparkles className="size-6" />
          <h1 className="text-2xl font-semibold">
            AI Research Assistant
          </h1>
        </div>

        <p className="text-sm text-muted-foreground">
          Ask questions about your uploaded documents and explore
          evidence-backed answers.
        </p>
      </div>

      {/* Conversation */}
      <div className="space-y-6">
        {messages.length === 0 && (
          <Card>
            <CardContent className="flex flex-col items-center gap-3 py-12 text-center">
              <MessageSquare className="size-10 text-muted-foreground" />

              <h2 className="text-lg font-semibold">
                Ask your first question
              </h2>

              <p className="max-w-md text-sm text-muted-foreground">
                Your assistant searches indexed documents and uses
                retrieved passages to generate answers with citations.
              </p>
            </CardContent>
          </Card>
        )}

        {messages.map((message) => (
          <div key={message.id} className="space-y-4">
            {/* User question */}
            <div className="flex justify-end">
              <div className="max-w-[85%] space-y-2 rounded-xl bg-muted px-4 py-3 text-sm">
                <p>{message.question}</p>
                <p className="text-xs text-muted-foreground">
                  Search: {message.scopeLabel}
                </p>
              </div>
            </div>

            {/* AI response */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Sparkles className="size-4" />
                  AI Answer
                </CardTitle>
              </CardHeader>

              <CardContent className="space-y-5">
                <AnswerText
                  answer={message.result.answer}
                  sources={message.result.sources}
                />

                {/* Citation verification */}
                <CitationVerification
                  results={message.result.citation_verification}
                  sources={message.result.sources}
                />

                {/* Existing cited evidence */}
                {message.result.citations.length > 0 && (
                  <div className="space-y-3 border-t pt-4">
                    <h3 className="text-sm font-semibold">
                      Cited evidence
                    </h3>

                    <div className="flex flex-wrap gap-2">
                      {message.result.citations.map((source) => (
                        <Link
                          key={source.source_id}
                          to={`/documents/${source.document_id}?page=${source.page_number}`}
                          className="rounded-lg border p-3 transition-colors hover:bg-accent"
                        >
                          <div className="flex items-center gap-2">
                            <Badge variant="secondary">
                              Source {source.source_id}
                            </Badge>

                            <ExternalLink className="size-3 text-muted-foreground" />
                          </div>

                          <p className="mt-2 text-sm font-medium">
                            {source.document_title}
                          </p>

                          <p className="text-xs text-muted-foreground">
                            Page {source.page_number}
                          </p>

                          <p className="mt-3 line-clamp-4 text-xs leading-5 text-muted-foreground">
                            {source.text}
                          </p>
                        </Link>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        ))}
      </div>

      {/* Question form */}
      <Card>
        <CardContent className="pt-5">
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Document selector */}
            <div className="space-y-2">
              <label
                htmlFor="document-selector"
                className="text-sm font-medium"
              >
                Search within
              </label>

              <select
                id="document-selector"
                value={selectedDocumentId}
                onChange={(event) =>
                  setSelectedDocumentId(event.target.value)
                }
                disabled={
                  loading ||
                  documentsLoading ||
                  !!documentsError
                }
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 disabled:opacity-50"
              >
                <option value="">All documents</option>

                {documents.map((document) => (
                  <option key={document.id} value={document.id}>
                    {document.title}
                  </option>
                ))}
              </select>

              {documentsLoading && (
                <p className="text-xs text-muted-foreground">
                  Loading available documents...
                </p>
              )}

              {documentsError && (
                <p className="text-xs text-destructive">
                  {documentsError}
                </p>
              )}

              {!documentsLoading &&
                !documentsError &&
                documents.length === 0 && (
                  <p className="text-xs text-muted-foreground">
                    No processed documents available yet.
                  </p>
                )}
            </div>

            <textarea
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="Ask a question about your documents..."
              disabled={loading}
              rows={3}
              className="flex w-full resize-y rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-xs outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-50"
            />

            {error && (
              <p className="text-sm text-destructive">
                {error}
              </p>
            )}

            <div className="flex items-center justify-between gap-3">
              <p className="text-xs text-muted-foreground">
                Answers are generated from indexed document passages.
              </p>

              <Button
                type="submit"
                disabled={
                  !question.trim() ||
                  loading ||
                  documentsLoading ||
                  !!documentsError ||
                  documents.length === 0
                }
              >
                {loading ? (
                  <>
                    <Loader2 className="size-4 animate-spin" />
                    Thinking...
                  </>
                ) : (
                  <>
                    <ArrowUp className="size-4" />
                    Ask
                  </>
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
