import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Download, FileWarning, Lock, Mail } from "lucide-react";
import { api, ApiError, publicPdfBlob, type PublicResume } from "@/lib/api";
import type { Content } from "@/lib/resume";
import { PublicChrome } from "@/components/public/PublicChrome";
import { ResumeDocument } from "@/components/resume/ResumeDocument";
import { PreviewPane } from "@/components/editor/PreviewPane";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";
import { Spinner } from "@/components/ui/Spinner";
import { formatRelative } from "@/lib/utils";

export default function PublicResumePage() {
  const { username = "", slug = "" } = useParams();
  const [password, setPassword] = useState("");
  const [passwordInput, setPasswordInput] = useState("");
  const [contactPassword, setContactPassword] = useState("");
  const [contactInput, setContactInput] = useState("");
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [pdfError, setPdfError] = useState("");
  const [downloading, setDownloading] = useState(false);

  const resume = useQuery<PublicResume>({
    queryKey: ["public-resume", username, slug, password, contactPassword],
    queryFn: () => api.publicResume(username, slug, password || undefined, contactPassword || undefined),
    retry: false,
  });

  const needsPassword =
    resume.error instanceof ApiError && (resume.error.code === "PASSWORD_REQUIRED" || resume.error.status === 401);
  const expired = resume.error instanceof ApiError && resume.error.status === 410;

  useEffect(() => {
    if (!resume.data || resume.data.mode !== "code") return;
    let objectUrl: string | null = null;
    let cancelled = false;
    setPdfError("");
    publicPdfBlob(username, slug, password || undefined, contactPassword || undefined)
      .then((blob) => {
        if (cancelled) return;
        objectUrl = URL.createObjectURL(blob);
        setPdfUrl(objectUrl);
      })
      .catch((error: Error) => {
        if (!cancelled) setPdfError(error.message);
      });
    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
      setPdfUrl(null);
    };
  }, [resume.data, username, slug, password, contactPassword]);

  const download = async () => {
    setDownloading(true);
    try {
      const blob = await publicPdfBlob(username, slug, password || undefined, contactPassword || undefined);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `${resume.data?.title ?? "resume"}.pdf`;
      anchor.click();
      window.setTimeout(() => URL.revokeObjectURL(url), 2000);
    } catch (error) {
      setPdfError(error instanceof Error ? error.message : "The PDF could not be downloaded");
    } finally {
      setDownloading(false);
    }
  };

  if (needsPassword) {
    return (
      <PublicChrome>
        <div className="mx-auto max-w-md">
          <div className="rounded-card border border-line bg-surface p-6 shadow-soft">
            <span className="grid h-10 w-10 place-items-center rounded-full border border-line bg-paper">
              <Lock size={16} />
            </span>
            <h1 className="mt-4 font-display text-3xl">This resume is locked.</h1>
            <p className="mt-1 text-sm leading-6 text-muted">
              Enter the password the owner shared with you. The link itself is still private.
            </p>
            <form
              className="mt-5 space-y-3"
              onSubmit={(event) => {
                event.preventDefault();
                setPassword(passwordInput);
              }}
            >
              <label className="block">
                <span className="mb-1 block font-mono text-[9px] uppercase tracking-[0.12em] text-muted">
                  Password
                </span>
                <input
                  type="password"
                  value={passwordInput}
                  onChange={(event) => setPasswordInput(event.target.value)}
                  autoFocus
                  className="focus-ring h-10 w-full rounded-field border border-line bg-paper px-3 text-sm"
                />
              </label>
              <Button type="submit" className="w-full" disabled={!passwordInput}>
                Open resume
              </Button>
              {password && resume.isError ? (
                <p className="text-xs text-danger">That password did not match. Try again.</p>
              ) : null}
            </form>
          </div>
        </div>
      </PublicChrome>
    );
  }

  if (resume.isLoading) {
    return (
      <PublicChrome>
        <div className="grid place-items-center py-24">
          <Spinner label="Opening the resume" />
        </div>
      </PublicChrome>
    );
  }

  if (expired) {
    return (
      <PublicChrome>
        <EmptyState
          icon={<FileWarning size={20} />}
          title="This link has expired"
          description="The owner set an end date for this resume. Ask them for a fresh link."
        />
      </PublicChrome>
    );
  }

  if (resume.isError || !resume.data) {
    return (
      <PublicChrome>
        <EmptyState
          icon={<FileWarning size={20} />}
          title="Resume not found"
          description="The link may have been revoked, or the address was typed differently."
          action={
            <Link to="/" className="text-sm underline decoration-line underline-offset-2">
              Back to Rezumiq
            </Link>
          }
        />
      </PublicChrome>
    );
  }

  const data = resume.data;

  return (
    <PublicChrome>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap items-center gap-2">
          <Badge tone="outline">@{data.username}</Badge>
          <span className="font-mono text-[10px] uppercase tracking-[0.1em] text-muted">
            Updated {formatRelative(data.updatedAt)}
          </span>
          {data.contactMasked ? <Badge tone="warning">Contact hidden</Badge> : null}
        </div>
        <div className="flex items-center gap-2">
          <Link to={`/${data.username}`} className="text-[12px] text-muted hover:text-ink">
            All resumes
          </Link>
          <Button size="sm" variant="dark" onClick={() => void download()} disabled={downloading}>
            <Download size={13} /> {downloading ? "Preparing..." : "PDF"}
          </Button>
        </div>
      </div>

      {data.contactLocked ? (
        <div className="mb-4 rounded-card border border-warning/25 bg-warning/5 p-4">
          <p className="flex items-center gap-2 text-[13px] font-medium text-warning">
            <Mail size={14} /> Contact details are locked
          </p>
          <p className="mt-1 text-[12px] text-muted">
            The resume is readable. Email and phone need the contact password from the owner.
          </p>
          <form
            className="mt-3 flex max-w-md gap-2"
            onSubmit={(event) => {
              event.preventDefault();
              setContactPassword(contactInput);
            }}
          >
            <input
              type="password"
              value={contactInput}
              onChange={(event) => setContactInput(event.target.value)}
              placeholder="Contact password"
              className="focus-ring h-9 min-w-0 flex-1 rounded-field border border-line bg-surface px-2.5 text-[13px]"
            />
            <Button size="sm" type="submit" disabled={!contactInput}>
              Unlock contact
            </Button>
          </form>
          {contactPassword ? (
            <p className="mt-2 text-[11px] text-danger">That password did not match the contact lock.</p>
          ) : null}
        </div>
      ) : null}

      {data.mode === "structured" && data.content ? (
        <div className="document-shadow overflow-hidden rounded-card border border-line bg-white">
          <ResumeDocument content={data.content as Content} />
        </div>
      ) : (
        <PreviewPane
          url={pdfUrl}
          loading={!pdfUrl && !pdfError}
          error={pdfError}
          pageCount={0}
          onDownload={() => void download()}
          className="min-h-[70vh]"
        />
      )}
    </PublicChrome>
  );
}
