import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { HelpCircle, LogOut, Menu, Search, Settings, UserRound } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/lib/auth";
import { initials } from "@/lib/utils";

const planLabel: Record<string, string> = {
  free: "Free Plan",
  season_pass: "Season Pass",
  pro: "Pro",
};

export function Topbar({ onMenu }: { onMenu: () => void }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [menu, setMenu] = useState(false);
  const [query, setQuery] = useState("");

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-3 border-b border-line bg-paper/90 px-4 backdrop-blur-md sm:px-6">
      <button
        type="button"
        onClick={onMenu}
        className="focus-ring grid h-9 w-9 place-items-center rounded-field border border-line bg-surface lg:hidden"
        aria-label="Open navigation"
      >
        <Menu size={17} />
      </button>

      <div className="hidden min-w-0 items-center gap-2 text-[13px] text-muted sm:flex">
        <span>Desk</span>
        <span className="text-line">/</span>
        <span className="text-ink">Workspace</span>
      </div>

      <div className="ml-auto hidden items-center gap-2 sm:flex">
        <form
          className="relative"
          onSubmit={(event) => {
            event.preventDefault();
            if (query.trim()) navigate(`/app/resumes?q=${encodeURIComponent(query.trim())}`);
          }}
        >
          <Search size={14} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
          <input
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search resumes..."
            className="focus-ring h-9 w-56 rounded-field border border-line bg-surface pl-8 pr-10 text-[13px] placeholder:text-muted/70"
            aria-label="Search resumes"
          />
          <kbd className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 rounded border border-line bg-paper px-1 py-0.5 font-mono text-[9px] text-muted">
            ↵
          </kbd>
        </form>
      </div>

      <div className="ml-auto flex items-center gap-1.5 sm:ml-0">
        <Badge tone="lime" className="hidden px-2.5 py-1 sm:inline-flex">
          {planLabel[user?.plan ?? "free"]}
        </Badge>
        <Link
          to="/app/ats"
          className="focus-ring hidden h-9 w-9 place-items-center rounded-field text-muted hover:bg-soft hover:text-ink sm:grid"
          aria-label="ATS checker"
          title="ATS checker"
        >
          <HelpCircle size={17} />
        </Link>
        <div className="relative">
          <button
            type="button"
            onClick={() => setMenu((value) => !value)}
            className="focus-ring flex h-9 items-center gap-2 rounded-field border border-line bg-surface pl-1 pr-2.5"
            aria-label="Account menu"
            aria-expanded={menu}
          >
            {user?.image ? (
              <img src={user.image} alt="" className="h-7 w-7 rounded-full object-cover" />
            ) : (
              <span className="grid h-7 w-7 place-items-center rounded-full bg-ink font-mono text-[10px] text-paper">
                {initials(user?.name || user?.email || "You")}
              </span>
            )}
            <span className="hidden max-w-28 truncate text-[12px] md:block">
              {user?.name || "Your account"}
            </span>
          </button>
          {menu ? (
            <>
              <button
                type="button"
                className="fixed inset-0 z-10 cursor-default"
                aria-label="Close account menu"
                onClick={() => setMenu(false)}
              />
              <div className="absolute right-0 z-20 mt-2 w-56 overflow-hidden rounded-card border border-line bg-surface shadow-lift">
                <div className="border-b border-line px-4 py-3">
                  <p className="truncate text-sm font-medium">{user?.name || user?.username}</p>
                  <p className="truncate text-xs text-muted">{user?.email}</p>
                </div>
                <div className="p-1.5">
                  <Link
                    to="/app/settings"
                    onClick={() => setMenu(false)}
                    className="flex items-center gap-2 rounded-field px-2.5 py-2 text-[13px] text-muted hover:bg-soft hover:text-ink"
                  >
                    <UserRound size={14} /> Account
                  </Link>
                  <Link
                    to="/app/settings"
                    onClick={() => setMenu(false)}
                    className="flex items-center gap-2 rounded-field px-2.5 py-2 text-[13px] text-muted hover:bg-soft hover:text-ink"
                  >
                    <Settings size={14} /> Settings
                  </Link>
                  <button
                    type="button"
                    onClick={async () => {
                      setMenu(false);
                      await logout();
                      navigate("/");
                    }}
                    className="flex w-full items-center gap-2 rounded-field px-2.5 py-2 text-left text-[13px] text-muted hover:bg-soft hover:text-ink"
                  >
                    <LogOut size={14} /> Sign out
                  </button>
                </div>
                <div className="border-t border-line p-2">
                  <Link to="/app/billing" onClick={() => setMenu(false)}>
                    <Button size="sm" className="w-full">
                      {user?.plan === "free" ? "Upgrade plan" : "Manage plan"}
                    </Button>
                  </Link>
                </div>
              </div>
            </>
          ) : null}
        </div>
      </div>
    </header>
  );
}
