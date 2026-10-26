import { useSearchParams } from "react-router-dom";
import { Activity, BarChart3, Database, FileStack, Users, Wallet } from "lucide-react";
import { useAuth } from "@/lib/auth";
import { PageHeader } from "@/components/ui/PageHeader";
import { Badge } from "@/components/ui/Badge";
import { cn } from "@/lib/utils";
import { AdminOverviewTab } from "./Overview";
import { AdminUsersTab } from "./Users";
import { AdminAiTab } from "./Ai";
import { AdminRevenueTab } from "./Revenue";
import { AdminContentTab } from "./Content";
import { AdminSystemTab } from "./System";

const tabs = [
  { id: "overview", label: "Overview", icon: Activity },
  { id: "users", label: "Users", icon: Users },
  { id: "ai", label: "AI", icon: BarChart3 },
  { id: "revenue", label: "Revenue", icon: Wallet },
  { id: "content", label: "Content", icon: FileStack },
  { id: "system", label: "System", icon: Database },
] as const;

type Tab = (typeof tabs)[number]["id"];

export default function AdminPage() {
  const { user } = useAuth();
  const [params, setParams] = useSearchParams();
  const requested = params.get("tab");
  const tab: Tab = tabs.some((item) => item.id === requested) ? (requested as Tab) : "overview";

  const setTab = (next: Tab) => {
    const search = new URLSearchParams(params);
    search.set("tab", next);
    setParams(search, { replace: true });
  };

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Admin / Control room"
        title="The whole system, in one place."
        description="Accounts, AI spend, payments, content, and the machine it all runs on. Every action here is audited by the API."
        actions={
          <div className="flex items-center gap-2">
            <Badge tone="dark">Staff only</Badge>
            <span className="font-mono text-[10px] text-muted">{user?.email}</span>
          </div>
        }
      />

      <div className="-mx-1 flex gap-1 overflow-x-auto border-b border-line px-1">
        {tabs.map((item) => (
          <button
            key={item.id}
            type="button"
            onClick={() => setTab(item.id)}
            className={cn(
              "flex shrink-0 items-center gap-1.5 whitespace-nowrap border-b-2 px-3 py-2.5 text-[12px] transition-colors",
              tab === item.id ? "border-ink font-medium text-ink" : "border-transparent text-muted hover:text-ink",
            )}
          >
            <item.icon size={13} /> {item.label}
          </button>
        ))}
      </div>

      {tab === "overview" ? <AdminOverviewTab /> : null}
      {tab === "users" ? <AdminUsersTab /> : null}
      {tab === "ai" ? <AdminAiTab /> : null}
      {tab === "revenue" ? <AdminRevenueTab /> : null}
      {tab === "content" ? <AdminContentTab /> : null}
      {tab === "system" ? <AdminSystemTab /> : null}
    </div>
  );
}
