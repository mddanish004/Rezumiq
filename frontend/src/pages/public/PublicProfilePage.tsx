import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowRight, FileText, Lock } from "lucide-react";
import { api, type PublicProfile as ProfileData } from "@/lib/api";
import { PublicChrome } from "@/components/public/PublicChrome";
import { Badge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";
import { Spinner } from "@/components/ui/Spinner";
import { formatRelative, initials } from "@/lib/utils";

export default function PublicProfilePage() {
  const { username = "" } = useParams();
  const profile = useQuery<ProfileData>({
    queryKey: ["public-profile", username],
    queryFn: () => api.publicProfile(username),
    retry: false,
  });

  return (
    <PublicChrome>
      {profile.isLoading ? (
        <div className="grid place-items-center py-24">
          <Spinner label="Opening the profile" />
        </div>
      ) : profile.isError || !profile.data ? (
        <EmptyState
          icon={<FileText size={20} />}
          title="No such profile"
          description="This address is not in use. A username can change, and a profile only exists while it has listed resumes."
          action={
            <Link to="/">
              <span className="text-sm underline decoration-line underline-offset-2">Back to Rezumiq</span>
            </Link>
          }
        />
      ) : (
        <div className="mx-auto max-w-2xl">
          <div className="flex flex-wrap items-center gap-4">
            <span className="grid h-16 w-16 place-items-center rounded-full border border-line bg-surface font-display text-2xl">
              {initials(profile.data.name) || "R"}
            </span>
            <div className="min-w-0">
              <p className="font-mono text-[9px] uppercase tracking-[0.16em] text-muted">Public profile</p>
              <h1 className="font-display text-4xl leading-tight">{profile.data.name}</h1>
              <p className="mt-0.5 font-mono text-[11px] text-muted">@{profile.data.username}</p>
            </div>
          </div>

          <div className="mt-10">
            <div className="flex items-baseline justify-between border-b border-line pb-2">
              <h2 className="font-display text-xl">Resumes</h2>
              <span className="font-mono text-[10px] uppercase tracking-[0.1em] text-muted">
                {profile.data.resumes.length} listed
              </span>
            </div>

            {profile.data.resumes.length ? (
              <ul className="divide-y divide-line">
                {profile.data.resumes.map((resume) => (
                  <li key={resume.slug}>
                    <Link
                      to={`/${profile.data!.username}/${resume.slug}`}
                      className="group flex items-center gap-3 py-4"
                    >
                      <span className="grid h-9 w-9 shrink-0 place-items-center rounded-field border border-line bg-surface">
                        <FileText size={15} />
                      </span>
                      <span className="min-w-0 flex-1">
                        <span className="block truncate text-[14px] font-medium group-hover:underline group-hover:decoration-line group-hover:underline-offset-4">
                          {resume.title}
                        </span>
                        <span className="mt-0.5 flex items-center gap-2 text-[11px] text-muted">
                          Updated {formatRelative(resume.updatedAt)}
                          {resume.hasPassword ? (
                            <span className="inline-flex items-center gap-1">
                              <Lock size={10} /> Password
                            </span>
                          ) : null}
                        </span>
                      </span>
                      <ArrowRight size={15} className="text-muted transition-transform group-hover:translate-x-0.5 group-hover:text-ink" />
                    </Link>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="mt-6 rounded-card border border-dashed border-line p-8 text-center">
                <p className="text-sm text-muted">Nothing is listed right now.</p>
                <Badge tone="outline" className="mt-2">Unlisted links still work</Badge>
              </div>
            )}
          </div>
        </div>
      )}
    </PublicChrome>
  );
}
