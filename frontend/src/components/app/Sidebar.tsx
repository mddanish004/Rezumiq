import { NavLink, Link } from "react-router-dom";
import {
  BarChart3,
  Briefcase,
  FileText,
  Gauge,
  LayoutDashboard,
  Settings,
  ShieldCheck,
  Sparkles,
  Upload,
  UserRound,
  Wallet,
  X,
} from "lucide-react";
import { Logo } from "@/components/ui/Logo";
import { cn } from "@/lib/utils";
import type { Usage } from "@/lib/api";
import { useAuth } from "@/lib/auth";

const workspace = [
  { label: "Dashboard", to: "/app", end: true, icon: LayoutDashboard },
  { label: "Resumes", to: "/app/resumes", icon: FileText },
  { label: "Import", to: "/app/import", icon: Upload },
  { label: "Jobs", to: "/app/jobs", icon: Briefcase },
  { label: "ATS Checker", to: "/app/ats", icon: Gauge },
  { label: "Analytics", to: "/app/analytics", icon: BarChart3 },
  { label: "Profile", to: "/app/profile", icon: UserRound },
];

const preferences = [
  { label: "Usage", to: "/app/usage", icon: Sparkles },
  { label: "Billing", to: "/app/billing", icon: Wallet },
  { label: "Settings", to: "/app/settings", icon: Settings },
];

const planLabel: Record<string, string> = {
  free: "Free tier",
  season_pass: "Season Pass",
  pro: "Pro",
};

export function Sidebar({
  usage,
  onClose,
  mobile = false,
}: {
  usage?: Usage;
  onClose?: () => void;
  mobile?: boolean;
}) {
  const { user } = useAuth();
  const plan = usage?.plan ?? "free";
  const resumeLimit = usage?.resumes.limit ?? 1000;
  const resumeUsed = usage?.resumes.used ?? 0;
  const quota = Math.min(100, Math.round((resumeUsed / Math.max(1, resumeLimit)) * 100));

  return (
    <div className="flex h-full flex-col border-r border-line bg-surface">
      <div className="flex h-16 items-center justify-between border-b border-line px-4">
        <Logo />
        {mobile ? (
          <button
            type="button"
            onClick={onClose}
            className="focus-ring grid h-8 w-8 place-items-center rounded-field text-muted hover:bg-soft"
            aria-label="Close navigation"
          >
            <X size={17} />
          </button>
        ) : null}
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-5">
        <p className="px-2 pb-2 font-mono text-[9px] uppercase tracking-[0.18em] text-muted">Workspace</p>
        <div className="space-y-0.5">
          {workspace.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              onClick={onClose}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-2.5 rounded-field px-2.5 py-2 text-[13px] transition-colors",
                  isActive
                    ? "bg-ink font-medium text-paper"
                    : "text-muted hover:bg-soft hover:text-ink",
                )
              }
            >
              <item.icon size={15} strokeWidth={1.7} />
              {item.label}
            </NavLink>
          ))}
        </div>

        <p className="px-2 pb-2 pt-7 font-mono text-[9px] uppercase tracking-[0.18em] text-muted">
          Preferences
        </p>
        <div className="space-y-0.5">
          {preferences.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={onClose}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-2.5 rounded-field px-2.5 py-2 text-[13px] transition-colors",
                  isActive
                    ? "bg-ink font-medium text-paper"
                    : "text-muted hover:bg-soft hover:text-ink",
                )
              }
            >
              <item.icon size={15} strokeWidth={1.7} />
              {item.label}
            </NavLink>
          ))}
        </div>

        {user?.isAdmin ? (
          <>
            <p className="px-2 pb-2 pt-7 font-mono text-[9px] uppercase tracking-[0.18em] text-muted">
              Admin
            </p>
            <NavLink
              to="/app/admin"
              onClick={onClose}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-2.5 rounded-field px-2.5 py-2 text-[13px] transition-colors",
                  isActive ? "bg-ink font-medium text-paper" : "text-muted hover:bg-soft hover:text-ink",
                )
              }
            >
              <ShieldCheck size={15} strokeWidth={1.7} />
              Control room
            </NavLink>
          </>
        ) : null}
      </nav>

      <div className="border-t border-line p-3">
        <div className="rounded-card border border-line bg-paper/70 p-3">
          <div className="flex items-center justify-between">
            <span className="font-mono text-[9px] uppercase tracking-[0.14em] text-muted">
              {planLabel[plan] ?? plan}
            </span>
            <Link to="/app/billing" className="text-[11px] font-medium underline decoration-line underline-offset-2">
              {plan === "free" ? "Upgrade" : "Manage"}
            </Link>
          </div>
          <div className="mt-2 flex items-baseline justify-between text-[11px]">
            <span className="text-muted">Resumes</span>
            <span className="font-mono">{resumeUsed} / {resumeLimit === 1000 ? "∞" : resumeLimit}</span>
          </div>
          <div className="mt-2 h-1 overflow-hidden rounded-full bg-line">
            <div className="h-full rounded-full bg-ink" style={{ width: `${quota}%` }} />
          </div>
          <p className="mt-2 text-[10px] text-muted">
            Resumes are never the limit. AI usage lives in{" "}
            <Link to="/app/usage" className="underline decoration-line underline-offset-2">
              Usage
            </Link>
            .
          </p>
        </div>
      </div>
    </div>
  );
}
