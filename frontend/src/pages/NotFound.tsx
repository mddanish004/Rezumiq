import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { PublicHeader } from "@/components/public/PublicHeader";
import { PublicFooter } from "@/components/public/PublicFooter";
import { Button } from "@/components/ui/Button";

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col bg-paper">
      <PublicHeader />
      <main className="flex flex-1 items-center justify-center px-5 py-20">
        <div className="max-w-md text-center">
          <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-muted">404 / Not found</p>
          <h1 className="mt-4 font-display text-5xl tracking-[-0.03em]">This page moved on.</h1>
          <p className="mt-3 text-sm leading-6 text-muted">
            The link may be old, or the resume may have been deleted. Try the workspace or start a new
            draft.
          </p>
          <div className="mt-7 flex justify-center gap-2">
            <Link to="/app">
              <Button size="sm">
                <ArrowLeft size={13} /> Workspace
              </Button>
            </Link>
            <Link to="/">
              <Button size="sm" variant="secondary">
                Home
              </Button>
            </Link>
          </div>
        </div>
      </main>
      <PublicFooter />
    </div>
  );
}
