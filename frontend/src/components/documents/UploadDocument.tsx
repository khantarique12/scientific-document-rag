import { useState, type FormEvent } from "react"
import { FileUp, Loader2 } from "lucide-react"

import { uploadDocument } from "@/api/documents"
import { Button } from "@/components/ui/button"

interface UploadDocumentProps {
  onUploaded: () => void
}

export function UploadDocument({ onUploaded }: UploadDocumentProps) {
  const [file, setFile] = useState<File | null>(null)
  const [title, setTitle] = useState("")
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (!file || !title.trim() || uploading) return

    setUploading(true)
    setError(null)
    setSuccess(false)

    try {
      await uploadDocument(file, title.trim())
      setFile(null)
      setTitle("")
      setSuccess(true)
      onUploaded()
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Upload failed",
      )
    } finally {
      setUploading(false)
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-4 rounded-lg border bg-card p-5"
    >
      <div>
        <h2 className="font-semibold">Upload PDF</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Add a research document to your library.
        </p>
      </div>

      <div className="space-y-2">
        <label htmlFor="document-title" className="text-sm font-medium">
          Document title
        </label>
        <input
          id="document-title"
          type="text"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          placeholder="Enter document title"
          required
          disabled={uploading}
          className="w-full rounded-md border bg-background px-3 py-2 text-sm"
        />
      </div>

      <div className="space-y-2">
        <label htmlFor="document-file" className="text-sm font-medium">
          PDF file
        </label>
        <input
          id="document-file"
          type="file"
          accept=".pdf,application/pdf"
          required
          disabled={uploading}
          onChange={(event) => {
            const selected = event.target.files?.[0] ?? null
            setFile(selected)
            setSuccess(false)
            setError(null)

            if (selected) {
              setTitle((current) =>
                current || selected.name.replace(/\.pdf$/i, ""),
              )
            }
          }}
          className="block w-full rounded-md border bg-background p-2 text-sm"
        />
      </div>

      {error && (
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      )}

      {success && (
        <p role="status" className="text-sm">
          Document uploaded successfully.
        </p>
      )}

      <Button
        type="submit"
        disabled={uploading || !file || !title.trim()}
      >
        {uploading ? (
          <Loader2 className="size-4 animate-spin" />
        ) : (
          <FileUp className="size-4" />
        )}
        {uploading ? "Uploading and processing..." : "Upload PDF"}
      </Button>
    </form>
  )
}