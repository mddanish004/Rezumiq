import { useEffect, useState } from "react";
import { FileWarning } from "lucide-react";

export function PdfFrame({
  url,
  title,
  className,
}: {
  url: string;
  title: string;
  className?: string;
}) {
  const [src, setSrc] = useState<string | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let objectUrl: string | null = null;
    let cancelled = false;
    setSrc(null);
    setError(false);
    fetch(url, { credentials: "include" })
      .then(async (response) => {
        if (!response.ok) throw new Error(`PDF request failed (${response.status})`);
        const blob = await response.blob();
        if (cancelled) return;
        objectUrl = URL.createObjectURL(blob);
        setSrc(objectUrl);
      })
      .catch(() => {
        if (!cancelled) setError(true);
      });
    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [url]);

  if (error) {
    return (
      <div className={`grid place-items-center rounded-field border border-line bg-surface p-6 ${className ?? ""}`}>
        <div className="text-center">
          <FileWarning size={20} className="mx-auto text-muted" />
          <p className="mt-2 text-sm text-muted">The PDF could not be loaded. Download it instead.</p>
        </div>
      </div>
    );
  }

  if (!src) {
    return (
      <div className={`grid place-items-center rounded-field border border-line bg-surface ${className ?? ""}`}>
        <span className="h-5 w-5 animate-spin rounded-full border-2 border-line border-t-ink" />
      </div>
    );
  }

  return <iframe title={title} src={src} className={className} />;
}
