import { useState } from "react"
import { Document as PDFDocument, Page, pdfjs } from "react-pdf"
import {
  ChevronLeft,
  ChevronRight,
  ZoomIn,
  ZoomOut,
} from "lucide-react"

import { Button } from "@/components/ui/button"

import "react-pdf/dist/Page/AnnotationLayer.css"
import "react-pdf/dist/Page/TextLayer.css"

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.mjs",
  import.meta.url,
).toString()

interface PDFViewerProps {
  fileUrl: string
  initialPage?: number
}

export function PDFViewer({
  fileUrl,
  initialPage = 1,
}: PDFViewerProps) {
  const [numPages, setNumPages] = useState(0)
  const [pageNumber, setPageNumber] = useState(initialPage)
  const [scale, setScale] = useState(1)

  function onLoadSuccess({
    numPages,
  }: {
    numPages: number
  }) {
    setNumPages(numPages)
    setPageNumber(
      Math.min(Math.max(initialPage, 1), numPages),
    )
  }

  return (
    <div className="overflow-hidden rounded-lg border bg-muted/20">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b bg-background p-3">
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="icon"
            disabled={pageNumber <= 1}
            onClick={() => setPageNumber((page) => page - 1)}
          >
            <ChevronLeft className="size-4" />
          </Button>

          <span className="min-w-24 text-center text-sm">
            {pageNumber} / {numPages || "—"}
          </span>

          <Button
            variant="outline"
            size="icon"
            disabled={!numPages || pageNumber >= numPages}
            onClick={() => setPageNumber((page) => page + 1)}
          >
            <ChevronRight className="size-4" />
          </Button>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="icon"
            disabled={scale <= 0.5}
            onClick={() =>
              setScale((value) =>
                Math.max(0.5, Number((value - 0.25).toFixed(2))),
              )
            }
          >
            <ZoomOut className="size-4" />
          </Button>

          <span className="min-w-12 text-center text-sm">
            {Math.round(scale * 100)}%
          </span>

          <Button
            variant="outline"
            size="icon"
            disabled={scale >= 2}
            onClick={() =>
              setScale((value) =>
                Math.min(2, Number((value + 0.25).toFixed(2))),
              )
            }
          >
            <ZoomIn className="size-4" />
          </Button>
        </div>
      </div>

      <div className="flex min-h-[600px] justify-center overflow-auto p-4">
        <PDFDocument
          file={fileUrl}
          onLoadSuccess={onLoadSuccess}
          loading={<p>Loading PDF...</p>}
          error={<p>Unable to load this PDF.</p>}
        >
          <Page
            pageNumber={pageNumber}
            scale={scale}
            renderTextLayer
            renderAnnotationLayer
          />
        </PDFDocument>
      </div>
    </div>
  )
}