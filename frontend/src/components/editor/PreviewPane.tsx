import { useEffect, useState } from "react";
import * as pdfjs from "pdfjs-dist";
import workerSrc from "pdfjs-dist/build/pdf.worker.min.mjs?url";
import { Download, FileWarning, Minus, Plus } from "lucide-react";
import { cn } from "@/lib/utils";

pdfjs.GlobalWorkerOptions.workerSrc = workerSrc;

export function PreviewPane({
  url,
  loading,
  error,
  pageCount: compiledPages,
  className,
  onDownload,
}: {
  url: string | null;
  loading: boolean;
  error: string;
  pageCount: number;
  className?: string;
  onDownload: () => void;
}) {
  const [pages, setPages] = useState<string[]>([]);
  const [renderError, setRenderError] = useState("");
  const [rendering, setRendering] = useState(false);
  const [zoom, setZoom] = useState(1);

  useEffect(() => {
    if (!url) return;
    let cancelled = false;
    const task = pdfjs.getDocument({ url });
    setRendering(true);
    setRenderError("");
    task.promise
      .then(async (document) => {
        const images: string[] = [];
        const ratio = Math.min(2, window.devicePixelRatio || 1);
        for (let number = 1; number <= Math.min(document.numPages, 3); number += 1) {
          const page = await document.getPage(number);
          const viewport = page.getViewport({ scale: 1.7 * ratio });
          const canvas = window.document.createElement("canvas");
          canvas.width = Math.floor(viewport.width);
          canvas.height = Math.floor(viewport.height);
          const context = canvas.getContext("2d");
          if (!context) continue;
          await page.render({ canvasContext: context, viewport, canvas }).promise;
          images.push(canvas.toDataURL("image/jpeg", 0.92));
        }
        if (!cancelled) setPages(images);
      })
      .catch((reason: Error) => {
        if (!cancelled && reason.name !== "AbortException") setRenderError("The preview could not be rendered.");
      })
      .finally(() => {
        if (!cancelled) setRendering(false);
      });
    return () => {
      cancelled = true;
      void task.destroy();
    };
  }, [url]);

  const pageCount = compiledPages || pages.length;
  const busy = loading || rendering;

  return (
    <div className={cn("flex min-h-0 flex-col", className)}>
      <div className="flex h-10 items-center justify-between rounded-t-card border border-line border-b-0 bg-surface px-3">
        <div className="flex items-center gap-2">
          <span className="font-mono text-[9px] uppercase tracking-[0.12em] text-muted">PDF preview</span>
          {pageCount ? (
            <span className="rounded-full border border-line bg-paper px-2 py-0.5 font-mono text-[9px] text-muted">
              {pageCount} {pageCount === 1 ? "page" : "pages"}
            </span>
          ) : null}
          {busy ? <span className="font-mono text-[9px] uppercase tracking-[0.1em] text-muted">Refreshing</span> : null}
        </div>
        <div className="flex items-center gap-0.5">
          <button
            type="button"
            onClick={() => setZoom((value) => Math.max(0.75, Math.round((value - 0.1) * 100) / 100))}
            className="focus-ring grid h-7 w-7 place-items-center rounded-field text-muted hover:bg-soft hover:text-ink"
            aria-label="Zoom out"
          >
            <Minus size={12} />
          </button>
          <span className="w-9 text-center font-mono text-[9px] text-muted">{Math.round(zoom * 100)}%</span>
          <button
            type="button"
            onClick={() => setZoom((value) => Math.min(1.6, Math.round((value + 0.1) * 100) / 100))}
            className="focus-ring grid h-7 w-7 place-items-center rounded-field text-muted hover:bg-soft hover:text-ink"
            aria-label="Zoom in"
          >
            <Plus size={12} />
          </button>
          <button
            type="button"
            onClick={onDownload}
            className="focus-ring grid h-7 w-7 place-items-center rounded-field text-muted hover:bg-soft hover:text-ink"
            aria-label="Download PDF"
          >
            <Download size={13} />
          </button>
        </div>
      </div>
      <div className="relative min-h-0 flex-1 overflow-auto rounded-b-card border border-line bg-[#E9E6DE] p-4">
        {error || renderError ? (
          <div className="mx-auto max-w-sm rounded-field border border-danger/20 bg-surface p-4 text-center">
            <FileWarning size={18} className="mx-auto text-danger" />
            <p className="mt-2 text-sm text-danger">{error || renderError}</p>
          </div>
        ) : pages.length ? (
          <div className="mx-auto flex w-fit flex-col gap-4" style={{ zoom }}>
            {pages.map((src, index) => (
              <img
                key={src.slice(-24)}
                src={src}
                alt={`Resume page ${index + 1}`}
                className="block w-[620px] max-w-full border border-line bg-white shadow-soft"
              />
            ))}
          </div>
        ) : (
          <div className="grid h-full min-h-[420px] place-items-center">
            <div className="text-center">
              <span className="mx-auto block h-5 w-5 animate-spin rounded-full border-2 border-line border-t-ink" />
              <p className="mt-3 font-mono text-[9px] uppercase tracking-[0.12em] text-muted">Reading the page</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
