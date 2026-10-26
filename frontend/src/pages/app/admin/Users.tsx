import { useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as Dialog from "@radix-ui/react-dialog";
import {
  Ban,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  FileText,
  LogOut,
  RotateCcw,
  Search,
  ShieldCheck,
  X,
} from "lucide-react";
import { toast } from "sonner";
import { api, type AdminUserDetail, type AdminUsersPage, type Plan } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import { formatDate, formatRelative, inr, usdFromMicros } from "@/lib/utils";
import { AdminMetric, EmptyRow, Panel, StatusBadge, formatNumber } from "./shared";

const planLabel: Record<Plan, string> = { free: "Free", season_pass: "Season Pass", pro: "Pro" };

export function AdminUsersTab() {
  const [query, setQuery] = useState("");
  const [appliedQuery, setAppliedQuery] = useState("");
  const [plan, setPlan] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<number | null>(null);

  const users = useQuery<AdminUsersPage>({
    queryKey: ["admin-users", { appliedQuery, plan, status, page }],
    queryFn: () => api.adminUsers({ q: appliedQuery, plan, status, page }),
  });

  const results = users.data;
  const pages = results ? Math.max(1, Math.ceil(results.total / results.pageSize)) : 1;

  return (
    <div className="space-y-4">
      <Panel
        title="People"
        description="Search by name, email, or username. Open a person to change their plan, sessions, or access."
      >
        <form
          className="flex flex-wrap items-end gap-2"
          onSubmit={(event) => {
            event.preventDefault();
            setPage(1);
            setAppliedQuery(query.trim());
          }}
        >
          <label className="min-w-[200px] flex-1">
            <span className="mb-1 block font-mono text-[9px] uppercase tracking-[0.1em] text-muted">Search</span>
            <div className="flex items-center gap-2 rounded-field border border-line bg-paper px-2.5">
              <Search size={13} className="text-muted" />
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Email or name"
                className="h-9 min-w-0 flex-1 bg-transparent text-[13px] outline-none"
              />
            </div>
          </label>
          <label>
            <span className="mb-1 block font-mono text-[9px] uppercase tracking-[0.1em] text-muted">Plan</span>
            <select
              value={plan}
              onChange={(event) => {
                setPlan(event.target.value);
                setPage(1);
              }}
              className="focus-ring h-9 rounded-field border border-line bg-paper px-2 text-[12px]"
            >
              <option value="">All plans</option>
              <option value="free">Free</option>
              <option value="season_pass">Season Pass</option>
              <option value="pro">Pro</option>
            </select>
          </label>
          <label>
            <span className="mb-1 block font-mono text-[9px] uppercase tracking-[0.1em] text-muted">Status</span>
            <select
              value={status}
              onChange={(event) => {
                setStatus(event.target.value);
                setPage(1);
              }}
              className="focus-ring h-9 rounded-field border border-line bg-paper px-2 text-[12px]"
            >
              <option value="">All statuses</option>
              <option value="active">Active</option>
              <option value="suspended">Suspended</option>
              <option value="guest">Guests</option>
            </select>
          </label>
          <Button size="sm" type="submit" variant="secondary">
            Search
          </Button>
        </form>

        <div className="mt-4 overflow-x-auto">
          <table className="w-full min-w-[820px] text-left text-[12px] [&_td]:pr-3 [&_th]:pr-3">
            <thead>
              <tr className="border-b border-line font-mono text-[9px] uppercase tracking-[0.1em] text-muted">
                <th className="pb-2 font-normal">Person</th>
                <th className="pb-2 font-normal">Plan</th>
                <th className="pb-2 text-right font-normal">Resumes</th>
                <th className="pb-2 text-right font-normal">AI runs</th>
                <th className="pb-2 font-normal">Last active</th>
                <th className="pb-2 font-normal">Joined</th>
                <th className="pb-2 font-normal">Status</th>
                <th className="pb-2" />
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {users.isLoading ? (
                <EmptyRow colSpan={8}>Loading people...</EmptyRow>
              ) : results?.users.length ? (
                results.users.map((user) => (
                  <tr
                    key={user.id}
                    className="cursor-pointer transition-colors hover:bg-paper/60"
                    onClick={() => setSelected(user.id)}
                  >
                    <td className="py-2.5">
                      <p className="font-medium">{user.name || "No name"}</p>
                      <p className="font-mono text-[10px] text-muted">{user.email}</p>
                    </td>
                    <td className="py-2.5">
                      <span className={user.plan === "free" ? "text-muted" : "font-medium"}>
                        {planLabel[user.plan]}
                      </span>
                    </td>
                    <td className="py-2.5 text-right font-mono">{user.resumes}</td>
                    <td className="py-2.5 text-right font-mono">{user.aiRuns}</td>
                    <td className="py-2.5 text-muted">{formatRelative(user.lastActiveAt) || "Never"}</td>
                    <td className="py-2.5 text-muted">{formatDate(user.createdAt)}</td>
                    <td className="py-2.5">
                      {user.suspendedAt ? (
                        <StatusBadge status="suspended" />
                      ) : user.isAnonymous ? (
                        <StatusBadge status="guest" />
                      ) : (
                        <StatusBadge status="active" />
                      )}
                    </td>
                    <td className="py-2.5 text-right">
                      <button
                        type="button"
                        className="focus-ring rounded px-2 py-1 text-[11px] text-muted hover:bg-soft hover:text-ink"
                        onClick={() => setSelected(user.id)}
                      >
                        Open
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <EmptyRow colSpan={8}>No people match those filters.</EmptyRow>
              )}
            </tbody>
          </table>
        </div>

        <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
          <p className="font-mono text-[10px] uppercase tracking-[0.1em] text-muted">
            {results ? `${results.total} people · page ${results.page} of ${pages}` : ""}
          </p>
          <div className="flex gap-1">
            <Button
              size="sm"
              variant="secondary"
              className="h-7 px-2"
              disabled={page <= 1}
              onClick={() => setPage((value) => Math.max(1, value - 1))}
              aria-label="Previous page"
            >
              <ChevronLeft size={12} />
            </Button>
            <Button
              size="sm"
              variant="secondary"
              className="h-7 px-2"
              disabled={page >= pages}
              onClick={() => setPage((value) => value + 1)}
              aria-label="Next page"
            >
              <ChevronRight size={12} />
            </Button>
          </div>
        </div>
      </Panel>

      <UserDrawer userId={selected} onClose={() => setSelected(null)} />
    </div>
  );
}

function useUserActions(userId: number | null, onClose: () => void) {
  const queryClient = useQueryClient();
  const refresh = async () => {
    await queryClient.invalidateQueries({ queryKey: ["admin-users"] });
    await queryClient.invalidateQueries({ queryKey: ["admin-overview"] });
  };

  const refreshDetail = async (detail: AdminUserDetail) => {
    queryClient.setQueryData(["admin-user", userId], detail);
    await refresh();
  };

  const close = () => {
    queryClient.removeQueries({ queryKey: ["admin-user", userId] });
    onClose();
  };

  const suspend = useMutation({
    mutationFn: (suspended: boolean) => api.adminSetSuspended(userId!, suspended),
    onSuccess: async (detail) => {
      await refreshDetail(detail);
      toast.success(detail.user.suspendedAt ? "Account suspended" : "Account restored");
    },
    onError: (error) => toast.error(error.message),
  });

  const sessions = useMutation({
    mutationFn: () => api.adminRevokeSessions(userId!),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["admin-user", userId] });
      toast.success("All sessions revoked");
    },
    onError: (error) => toast.error(error.message),
  });

  const usage = useMutation({
    mutationFn: () => api.adminResetUsage(userId!),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["admin-user", userId] });
      toast.success("Usage counters reset");
    },
    onError: (error) => toast.error(error.message),
  });

  const grant = useMutation({
    mutationFn: ({ plan, months }: { plan: "season_pass" | "pro"; months: number }) =>
      api.adminGrantSubscription(userId!, plan, months),
    onSuccess: async (detail) => {
      await refreshDetail(detail);
      toast.success("Complimentary subscription granted");
    },
    onError: (error) => toast.error(error.message),
  });

  const revoke = useMutation({
    mutationFn: (subscriptionId: string) => api.adminRevokeSubscription(userId!, subscriptionId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["admin-user", userId] });
      await refresh();
      toast.success("Subscription revoked");
    },
    onError: (error) => toast.error(error.message),
  });

  return { suspend, sessions, usage, grant, revoke, close };
}

function UserDrawer({ userId, onClose }: { userId: number | null; onClose: () => void }) {
  const detail = useQuery<AdminUserDetail>({
    queryKey: ["admin-user", userId],
    queryFn: () => api.adminUser(userId!),
    enabled: userId !== null,
  });
  const actions = useUserActions(userId, onClose);
  const [grantPlan, setGrantPlan] = useState<"season_pass" | "pro">("pro");
  const [months, setMonths] = useState(1);

  return (
    <Dialog.Root
      open={userId !== null}
      onOpenChange={(open) => {
        if (!open) actions.close();
      }}
    >
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-ink/25 backdrop-blur-[2px]" />
        <Dialog.Content className="fixed right-0 top-0 z-50 flex h-full w-[min(620px,100vw)] flex-col border-l border-line bg-surface shadow-lift">
          <div className="flex items-start justify-between border-b border-line px-5 py-4">
            <div className="min-w-0">
              <Dialog.Title className="truncate font-display text-2xl">
                {detail.data?.user.name || "Person"}
              </Dialog.Title>
              <Dialog.Description className="mt-1 truncate font-mono text-[11px] text-muted">
                {detail.data?.user.email ?? "Loading account"}
              </Dialog.Description>
            </div>
            <Dialog.Close asChild>
              <button
                type="button"
                className="focus-ring grid h-8 w-8 shrink-0 place-items-center rounded-field text-muted hover:bg-soft"
                aria-label="Close person"
              >
                <X size={16} />
              </button>
            </Dialog.Close>
          </div>

          <div className="flex-1 overflow-y-auto p-5">
            {detail.isLoading || !detail.data ? (
              <Spinner label="Loading the account" />
            ) : detail.isError ? (
              <p className="text-sm text-danger">That account could not be loaded.</p>
            ) : (
              <UserBody
                data={detail.data}
                grantPlan={grantPlan}
                setGrantPlan={setGrantPlan}
                months={months}
                setMonths={setMonths}
                onSuspend={() => actions.suspend.mutate(!detail.data.user.suspendedAt)}
                suspendPending={actions.suspend.isPending}
                onSessions={() => {
                  if (window.confirm("Sign this person out on every device?")) actions.sessions.mutate();
                }}
                sessionsPending={actions.sessions.isPending}
                onResetUsage={() => {
                  if (window.confirm("Reset this person's AI usage counters for the current period?")) {
                    actions.usage.mutate();
                  }
                }}
                usagePending={actions.usage.isPending}
                onGrant={() => actions.grant.mutate({ plan: grantPlan, months })}
                grantPending={actions.grant.isPending}
                onRevoke={(id) => actions.revoke.mutate(id)}
                revokePending={actions.revoke.isPending}
              />
            )}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

function UserBody({
  data,
  grantPlan,
  setGrantPlan,
  months,
  setMonths,
  onSuspend,
  suspendPending,
  onSessions,
  sessionsPending,
  onResetUsage,
  usagePending,
  onGrant,
  grantPending,
  onRevoke,
  revokePending,
}: {
  data: AdminUserDetail;
  grantPlan: "season_pass" | "pro";
  setGrantPlan: (plan: "season_pass" | "pro") => void;
  months: number;
  setMonths: (months: number) => void;
  onSuspend: () => void;
  suspendPending: boolean;
  onSessions: () => void;
  sessionsPending: boolean;
  onResetUsage: () => void;
  usagePending: boolean;
  onGrant: () => void;
  grantPending: boolean;
  onRevoke: (id: string) => void;
  revokePending: boolean;
}) {
  const { user } = data;
  const counters = [
    { label: "Resumes", value: data.usage.resumes },
    { label: "Tailor", value: data.usage.tailor },
    { label: "Edit", value: data.usage.edit },
    { label: "Import", value: data.usage.import },
    { label: "Draft", value: data.usage.draft },
  ];

  return (
    <div className="space-y-5">
      {user.suspendedAt ? (
        <div className="rounded-field border border-danger/20 bg-danger/5 px-3 py-2 text-[12px] text-danger">
          Suspended {formatRelative(user.suspendedAt)}. They cannot sign in or use the API.
        </div>
      ) : null}

      <div className="flex flex-wrap items-center gap-1.5">
        <span className="rounded-full border border-line bg-paper px-2 py-0.5 font-mono text-[9px] uppercase tracking-[0.1em]">
          {planLabel[user.plan]}
        </span>
        <StatusBadge status={user.suspendedAt ? "suspended" : user.isAnonymous ? "guest" : "active"} />
        <span className="rounded-full border border-line px-2 py-0.5 font-mono text-[9px] uppercase tracking-[0.1em] text-muted">
          {user.emailVerified ? "Email verified" : "Email unverified"}
        </span>
        <span className="ml-auto font-mono text-[10px] text-muted">@{user.username}</span>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <AdminMetric label="Resumes" value={data.resumes.length} hint={`${data.jobs} jobs saved`} />
        <AdminMetric label="AI runs" value={data.ai.runs} hint={`${usdFromMicros(data.ai.costUsdMicros)} spent`} />
        <AdminMetric label="Share links" value={data.shareLinks} hint={`${data.shareViews} views`} />
        <AdminMetric label="Sessions" value={data.sessions.length} hint={`Joined ${formatDate(user.createdAt)}`} />
      </div>

      <div className="flex flex-wrap gap-2">
        <Button size="sm" variant={user.suspendedAt ? "secondary" : "danger"} onClick={onSuspend} disabled={suspendPending}>
          {user.suspendedAt ? <CheckCircle2 size={13} /> : <Ban size={13} />}
          {user.suspendedAt ? "Restore access" : "Suspend account"}
        </Button>
        <Button size="sm" variant="secondary" onClick={onSessions} disabled={sessionsPending || !data.sessions.length}>
          <LogOut size={13} /> Revoke sessions
        </Button>
        <Button size="sm" variant="secondary" onClick={onResetUsage} disabled={usagePending}>
          <RotateCcw size={13} /> Reset usage
        </Button>
      </div>

      <div>
        <p className="font-mono text-[9px] uppercase tracking-[0.12em] text-muted">Usage this period</p>
        <div className="mt-2 grid grid-cols-2 gap-2 sm:grid-cols-5">
          {counters.map((counter) => (
            <div key={counter.label} className="rounded-field border border-line bg-paper/50 p-2">
              <p className="text-[10px] text-muted">{counter.label}</p>
              <p className="font-mono text-[12px]">
                {counter.value.used} / {counter.value.limit >= 1000 ? "∞" : counter.value.limit}
              </p>
            </div>
          ))}
        </div>
        <p className="mt-1.5 text-[10px] text-muted">
          Period {formatDate(data.usage.periodStart)} to {formatDate(data.usage.periodEnd)}
          {data.usage.ownAiKey ? " · own AI key" : ""}
        </p>
      </div>

      <div className="rounded-field border border-line bg-paper/40 p-3">
        <div className="flex items-center gap-2">
          <ShieldCheck size={13} className="text-forest" />
          <p className="text-[12px] font-medium">Grant a complimentary subscription</p>
        </div>
        <div className="mt-2 flex flex-wrap items-center gap-2">
          <select
            value={grantPlan}
            onChange={(event) => setGrantPlan(event.target.value as "season_pass" | "pro")}
            className="focus-ring h-8 rounded-field border border-line bg-surface px-2 text-[12px]"
            aria-label="Grant plan"
          >
            <option value="season_pass">Season Pass</option>
            <option value="pro">Pro</option>
          </select>
          <select
            value={months}
            onChange={(event) => setMonths(Number(event.target.value))}
            className="focus-ring h-8 rounded-field border border-line bg-surface px-2 text-[12px]"
            aria-label="Grant months"
          >
            {[1, 3, 6, 12].map((value) => (
              <option key={value} value={value}>
                {value} {value === 1 ? "month" : "months"}
              </option>
            ))}
          </select>
          <Button size="sm" className="h-8" onClick={onGrant} disabled={grantPending}>
            {grantPending ? "Granting..." : "Grant"}
          </Button>
        </div>
      </div>

      {data.subscriptions.length ? (
        <div>
          <p className="font-mono text-[9px] uppercase tracking-[0.12em] text-muted">Subscriptions</p>
          <div className="mt-2 space-y-2">
            {data.subscriptions.map((subscription) => (
              <div
                key={subscription.id}
                className="flex flex-wrap items-center gap-2 rounded-field border border-line bg-paper/40 px-3 py-2"
              >
                <span className="text-[12px] font-medium">{planLabel[subscription.plan]}</span>
                <StatusBadge status={subscription.status} />
                {subscription.complimentary ? (
                  <span className="font-mono text-[9px] uppercase tracking-[0.08em] text-muted">Complimentary</span>
                ) : null}
                <span className="text-[11px] text-muted">
                  {subscription.currentPeriodEnd ? `until ${formatDate(subscription.currentPeriodEnd)}` : ""}
                </span>
                {subscription.status === "active" || subscription.status === "created" ? (
                  <button
                    type="button"
                    className="focus-ring ml-auto rounded px-2 py-1 text-[11px] text-danger hover:bg-danger/5"
                    disabled={revokePending}
                    onClick={() => {
                      if (window.confirm("Revoke this subscription now?")) onRevoke(subscription.id);
                    }}
                  >
                    Revoke
                  </button>
                ) : null}
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {data.payments.length ? (
        <div>
          <p className="font-mono text-[9px] uppercase tracking-[0.12em] text-muted">Payments</p>
          <table className="mt-2 w-full text-left text-[12px]">
            <tbody className="divide-y divide-line">
              {data.payments.map((payment) => (
                <tr key={payment.id}>
                  <td className="py-2">{inr(payment.amountPaise)}</td>
                  <td className="py-2">
                    <StatusBadge status={payment.status} />
                  </td>
                  <td className="py-2 text-muted">{payment.method || "—"}</td>
                  <td className="py-2 text-right font-mono text-[10px] text-muted">
                    {formatDate(payment.createdAt)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      <div>
        <p className="font-mono text-[9px] uppercase tracking-[0.12em] text-muted">
          Resumes · {formatNumber(data.resumes.length)}
        </p>
        <div className="mt-2 space-y-1.5">
          {data.resumes.length ? (
            data.resumes.map((resume) => (
              <Link
                key={resume.id}
                to={`/app/resumes/${resume.id}/edit`}
                className="flex items-center gap-2 rounded-field border border-line bg-paper/40 px-3 py-2 hover:border-ink/20"
              >
                <FileText size={13} className="text-muted" />
                <span className="min-w-0 flex-1 truncate text-[12px]">{resume.title}</span>
                <span className="font-mono text-[9px] uppercase tracking-[0.08em] text-muted">
                  {resume.mode} · v{resume.versions}
                </span>
                {resume.deletedAt ? <StatusBadge status="deleted" /> : null}
                {resume.archivedAt ? <StatusBadge status="archived" /> : null}
              </Link>
            ))
          ) : (
            <p className="text-[12px] text-muted">No resumes yet.</p>
          )}
        </div>
      </div>

      <div className="border-t border-line pt-3 text-[10px] text-muted">
        Joined {formatDate(user.createdAt)} · last updated {formatRelative(user.updatedAt)}
        {data.accounts.length ? ` · via ${data.accounts.map((account) => account.providerId).join(", ")}` : ""}
        {data.ai.lastRunAt ? ` · last AI run ${formatRelative(data.ai.lastRunAt)}` : ""}
      </div>
    </div>
  );
}
