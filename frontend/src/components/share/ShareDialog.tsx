import { useState } from "react";
import * as Dialog from "@radix-ui/react-dialog";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, Copy, ExternalLink, Link2, Lock, Plus, Trash2, X } from "lucide-react";
import { toast } from "sonner";
import { api, type ShareLink } from "@/lib/api";
import type { Version } from "@/lib/resume";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import { cn, formatRelative } from "@/lib/utils";

export function ShareDialog({
  open,
  onOpenChange,
  resumeId,
  resumeTitle,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  resumeId: string;
  resumeTitle: string;
}) {
  const queryClient = useQueryClient();
  const [creating, setCreating] = useState(false);
  const [copied, setCopied] = useState("");

  const links = useQuery<ShareLink[]>({
    queryKey: ["share-links", resumeId],
    queryFn: () => api.shareLinks(resumeId),
    enabled: open,
  });

  const copy = async (link: ShareLink) => {
    try {
      await navigator.clipboard.writeText(link.url);
      setCopied(link.id);
      window.setTimeout(() => setCopied(""), 1600);
      toast.success("Link copied");
    } catch {
      toast.error("Copy failed. Select the address manually.");
    }
  };

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-ink/30 backdrop-blur-[2px]" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 flex max-h-[86vh] w-[min(620px,calc(100vw-2rem))] -translate-x-1/2 -translate-y-1/2 flex-col rounded-card border border-line bg-surface shadow-lift">
          <div className="flex items-start justify-between border-b border-line px-5 py-4">
            <div>
              <Dialog.Title className="flex items-center gap-2 font-display text-2xl">
                <Link2 size={17} /> Share
              </Dialog.Title>
              <Dialog.Description className="mt-1 text-xs text-muted">
                A public page for “{resumeTitle}”. Revoke a link any time; views stop counting immediately.
              </Dialog.Description>
            </div>
            <Dialog.Close asChild>
              <button
                type="button"
                className="focus-ring grid h-8 w-8 place-items-center rounded-field text-muted hover:bg-soft"
                aria-label="Close share"
              >
                <X size={16} />
              </button>
            </Dialog.Close>
          </div>

          <div className="flex-1 overflow-y-auto p-5">
            {links.isLoading ? (
              <Spinner label="Loading links" />
            ) : (
              <div className="space-y-3">
                {(links.data ?? []).map((link) => (
                  <LinkRow
                    key={link.id}
                    link={link}
                    copied={copied === link.id}
                    onCopy={() => void copy(link)}
                  />
                ))}
                {!links.data?.length && !creating ? (
                  <div className="rounded-field border border-dashed border-line p-5 text-center">
                    <p className="text-sm font-medium">No public link yet</p>
                    <p className="mt-1 text-xs text-muted">
                      A link is a snapshot of the current version. Update it without changing the address.
                    </p>
                    <Button size="sm" className="mt-3" onClick={() => setCreating(true)}>
                      <Plus size={13} /> Create a link
                    </Button>
                  </div>
                ) : null}
              </div>
            )}

            {creating || links.data?.length ? (
              <div className="mt-4 border-t border-line pt-4">
                <CreateForm
                  resumeId={resumeId}
                  collapsed={Boolean(links.data?.length) && !creating}
                  onNew={() => setCreating(true)}
                  onCreated={() => {
                    setCreating(false);
                    void queryClient.invalidateQueries({ queryKey: ["share-links", resumeId] });
                    void queryClient.invalidateQueries({ queryKey: ["analytics"] });
                  }}
                />
              </div>
            ) : null}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

function LinkRow({ link, copied, onCopy }: { link: ShareLink; copied: boolean; onCopy: () => void }) {
  const queryClient = useQueryClient();
  const [showPassword, setShowPassword] = useState(false);
  const [password, setPassword] = useState("");

  const refresh = async () => {
    await queryClient.invalidateQueries({ queryKey: ["share-links", link.resumeId] });
    await queryClient.invalidateQueries({ queryKey: ["analytics"] });
  };

  const update = useMutation({
    mutationFn: (body: Record<string, unknown>) => api.updateShareLink(link.id, body),
    onSuccess: refresh,
    onError: (error) => toast.error(error.message),
  });

  const remove = useMutation({
    mutationFn: () => api.deleteShareLink(link.id),
    onSuccess: async () => {
      await refresh();
      toast.success("Link revoked");
    },
    onError: (error) => toast.error(error.message),
  });

  return (
    <div className="rounded-field border border-line bg-paper/40 p-3">
      <div className="flex flex-wrap items-center gap-2">
        <code className="min-w-0 flex-1 truncate rounded bg-surface px-2 py-1 font-mono text-[11px] text-ink">
          {link.url.replace(/^https?:\/\//, "")}
        </code>
        <Button size="sm" variant="secondary" className="h-7 px-2 text-[11px]" onClick={onCopy}>
          {copied ? <Check size={11} /> : <Copy size={11} />} {copied ? "Copied" : "Copy"}
        </Button>
        <a href={link.url} target="_blank" rel="noreferrer">
          <Button size="sm" variant="ghost" className="h-7 px-2 text-[11px]">
            <ExternalLink size={11} /> Open
          </Button>
        </a>
      </div>

      <div className="mt-2 flex flex-wrap items-center gap-1.5">
        <Badge tone={link.isListed ? "lime" : "outline"}>
          {link.isListed ? "On profile" : "Unlisted"}
        </Badge>
        <Badge tone={link.showContact ? "success" : "outline"}>
          {link.showContact ? "Contact shown" : "Contact hidden"}
        </Badge>
        {link.hasPassword ? (
          <Badge tone="warning">
            <Lock size={10} /> Password
          </Badge>
        ) : null}
        <span className="ml-auto font-mono text-[9px] uppercase tracking-[0.1em] text-muted">
          {link.viewCount} {link.viewCount === 1 ? "view" : "views"} · {formatRelative(link.lastViewedAt) || "not opened"}
        </span>
      </div>

      <div className="mt-2 flex flex-wrap items-center gap-1.5">
        <button
          type="button"
          onClick={() => update.mutate({ isListed: !link.isListed })}
          className={cn(
            "focus-ring rounded-field border px-2 py-1 text-[11px]",
            link.isListed ? "border-line bg-surface text-ink" : "border-line text-muted hover:text-ink",
          )}
        >
          {link.isListed ? "Remove from profile" : "List on profile"}
        </button>
        <button
          type="button"
          onClick={() => update.mutate({ showContact: !link.showContact })}
          className="focus-ring rounded-field border border-line px-2 py-1 text-[11px] text-muted hover:text-ink"
        >
          {link.showContact ? "Hide contact" : "Show contact"}
        </button>
        <button
          type="button"
          onClick={() => setShowPassword((value) => !value)}
          className="focus-ring rounded-field border border-line px-2 py-1 text-[11px] text-muted hover:text-ink"
        >
          {link.hasPassword ? "Change password" : "Add password"}
        </button>
        <button
          type="button"
          onClick={() => {
            if (window.confirm("Revoke this link? The public page stops working immediately.")) {
              remove.mutate();
            }
          }}
          className="focus-ring ml-auto grid h-7 w-7 place-items-center rounded-field text-muted hover:bg-danger/5 hover:text-danger"
          aria-label="Revoke link"
        >
          <Trash2 size={12} />
        </button>
      </div>

      {showPassword ? (
        <form
          className="mt-2 flex gap-1.5"
          onSubmit={(event) => {
            event.preventDefault();
            update.mutate({ password: password || null });
            setPassword("");
            setShowPassword(false);
          }}
        >
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder={link.hasPassword ? "New password (blank clears it)" : "Password"}
            className="focus-ring h-8 min-w-0 flex-1 rounded-field border border-line bg-surface px-2 text-[12px]"
          />
          <Button size="sm" type="submit" className="h-8">
            Save
          </Button>
        </form>
      ) : null}
    </div>
  );
}

function CreateForm({
  resumeId,
  collapsed,
  onNew,
  onCreated,
}: {
  resumeId: string;
  collapsed: boolean;
  onNew: () => void;
  onCreated: () => void;
}) {
  const [expanded, setExpanded] = useState(!collapsed);
  const [slug, setSlug] = useState("");
  const [listed, setListed] = useState(false);
  const [showContact, setShowContact] = useState(false);
  const [password, setPassword] = useState("");
  const [expires, setExpires] = useState("");
  const [pinnedVersionId, setPinnedVersionId] = useState("");

  const versions = useQuery<Version[]>({
    queryKey: ["versions", resumeId],
    queryFn: () => api.versions(resumeId),
    enabled: expanded,
  });

  const create = useMutation({
    mutationFn: () =>
      api.createShareLink(resumeId, {
        ...(slug.trim() ? { slug: slug.trim().toLowerCase() } : {}),
        isListed: listed,
        showContact,
        ...(password ? { password } : {}),
        ...(pinnedVersionId ? { pinnedVersionId } : {}),
        ...(expires ? { expiresAt: new Date(`${expires}T23:59:59`).toISOString() } : {}),
      }),
    onSuccess: () => {
      setSlug("");
      setPassword("");
      setExpires("");
      setListed(false);
      setShowContact(false);
      setPinnedVersionId("");
      setExpanded(false);
      onCreated();
      toast.success("Share link created");
    },
    onError: (error) => toast.error(error.message),
  });

  if (!expanded) {
    return (
      <Button
        size="sm"
        variant="secondary"
        onClick={() => {
          setExpanded(true);
          onNew();
        }}
      >
        <Plus size={13} /> New link
      </Button>
    );
  }

  return (
    <form
      className="space-y-3"
      onSubmit={(event) => {
        event.preventDefault();
        create.mutate();
      }}
    >
      <div className="flex items-center justify-between">
        <p className="font-mono text-[9px] uppercase tracking-[0.12em] text-muted">New link</p>
        <button
          type="button"
          onClick={() => setExpanded(false)}
          className="focus-ring rounded px-1 text-[11px] text-muted hover:text-ink"
        >
          Hide
        </button>
      </div>

      <div className="grid gap-2 sm:grid-cols-2">
        <label className="block">
          <span className="mb-1 block font-mono text-[9px] uppercase tracking-[0.1em] text-muted">
            Custom slug (optional)
          </span>
          <input
            value={slug}
            onChange={(event) => setSlug(event.target.value)}
            placeholder="backend-2026"
            pattern="[a-z0-9-]{3,30}"
            className="focus-ring h-9 w-full rounded-field border border-line bg-paper px-2.5 font-mono text-[12px]"
          />
        </label>
        <label className="block">
          <span className="mb-1 block font-mono text-[9px] uppercase tracking-[0.1em] text-muted">
            Expires (optional)
          </span>
          <input
            type="date"
            value={expires}
            onChange={(event) => setExpires(event.target.value)}
            className="focus-ring h-9 w-full rounded-field border border-line bg-paper px-2.5 text-[12px]"
          />
        </label>
        <label className="block">
          <span className="mb-1 block font-mono text-[9px] uppercase tracking-[0.1em] text-muted">
            Password (optional)
          </span>
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Leave blank for a public link"
            className="focus-ring h-9 w-full rounded-field border border-line bg-paper px-2.5 text-[12px]"
          />
        </label>
        <label className="block">
          <span className="mb-1 block font-mono text-[9px] uppercase tracking-[0.1em] text-muted">
            Pin a version (optional)
          </span>
          <select
            value={pinnedVersionId}
            onChange={(event) => setPinnedVersionId(event.target.value)}
            className="focus-ring h-9 w-full rounded-field border border-line bg-paper px-2 text-[12px]"
          >
            <option value="">Always the latest head</option>
            {(versions.data ?? []).map((version) => (
              <option key={version.id} value={version.id}>
                {version.label ?? `${version.kind} · ${formatRelative(version.createdAt)}`}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="flex flex-wrap items-center gap-3 text-[12px]">
        <label className="flex items-center gap-1.5">
          <input type="checkbox" checked={listed} onChange={(event) => setListed(event.target.checked)} className="accent-[#1F5A46]" />
          List on my public profile
        </label>
        <label className="flex items-center gap-1.5">
          <input
            type="checkbox"
            checked={showContact}
            onChange={(event) => setShowContact(event.target.checked)}
            className="accent-[#1F5A46]"
          />
          Show email and phone
        </label>
      </div>

      <Button size="sm" type="submit" disabled={create.isPending}>
        <Link2 size={13} /> {create.isPending ? "Creating..." : "Create link"}
      </Button>
    </form>
  );
}
