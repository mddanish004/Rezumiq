import { useState } from "react";
import { Outlet } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";
import { api, type Usage } from "@/lib/api";
import { cn } from "@/lib/utils";

export function AppShell() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const usageQuery = useQuery<Usage>({ queryKey: ["usage"], queryFn: api.usage, retry: false });

  return (
    <div className="min-h-screen bg-paper lg:grid lg:grid-cols-[248px_minmax(0,1fr)]">
      <aside className="sticky top-0 hidden h-screen lg:block">
        <Sidebar usage={usageQuery.data} />
      </aside>

      <div className={cn("min-w-0", mobileOpen && "overflow-hidden")}>
        <Topbar onMenu={() => setMobileOpen(true)} />
        <main className="mx-auto w-full max-w-[1320px] px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
          <Outlet />
        </main>
      </div>

      {mobileOpen ? (
        <div className="fixed inset-0 z-50 lg:hidden" role="dialog" aria-modal="true">
          <button
            type="button"
            className="absolute inset-0 bg-ink/30 backdrop-blur-sm"
            aria-label="Close navigation"
            onClick={() => setMobileOpen(false)}
          />
          <div className="relative h-full w-[280px] max-w-[85vw] bg-surface shadow-lift">
            <Sidebar usage={usageQuery.data} mobile onClose={() => setMobileOpen(false)} />
          </div>
        </div>
      ) : null}
    </div>
  );
}
