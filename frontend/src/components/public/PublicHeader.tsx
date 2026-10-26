import { useState } from "react";
import { Link, NavLink } from "react-router-dom";
import { Menu, X, ArrowUpRight } from "lucide-react";
import { Logo } from "@/components/ui/Logo";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/lib/auth";
import { cn } from "@/lib/utils";

const links = [
  { label: "Features", href: "/#features" },
  { label: "Templates", href: "/#templates" },
  { label: "ATS Checker", href: "/ats-checker" },
  { label: "Pricing", href: "/#pricing" },
];

export function PublicHeader() {
  const [open, setOpen] = useState(false);
  const { user } = useAuth();

  return (
    <header className="sticky top-0 z-40 border-b border-line/70 bg-paper/85 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-[1240px] items-center justify-between px-5 lg:px-8">
        <Logo />
        <nav className="hidden items-center gap-7 lg:flex" aria-label="Main">
          {links.map((link) =>
            link.href.startsWith("/#") ? (
              <a
                key={link.label}
                href={link.href}
                className="text-[13px] text-muted transition-colors hover:text-ink"
              >
                {link.label}
              </a>
            ) : (
              <NavLink
                key={link.label}
                to={link.href}
                className="text-[13px] text-muted transition-colors hover:text-ink"
              >
                {link.label}
              </NavLink>
            ),
          )}
        </nav>
        <div className="hidden items-center gap-2 lg:flex">
          {user ? (
            <Link to="/app">
              <Button size="sm">
                Open workspace <ArrowUpRight size={14} />
              </Button>
            </Link>
          ) : (
            <>
              <Link to="/login">
                <Button variant="ghost" size="sm">
                  Sign in
                </Button>
              </Link>
              <Link to="/signup">
                <Button size="sm">
                  Start free <ArrowUpRight size={14} />
                </Button>
              </Link>
            </>
          )}
        </div>
        <button
          type="button"
          className="focus-ring grid h-10 w-10 place-items-center rounded-field border border-line bg-surface lg:hidden"
          onClick={() => setOpen((value) => !value)}
          aria-label={open ? "Close menu" : "Open menu"}
          aria-expanded={open}
        >
          {open ? <X size={18} /> : <Menu size={18} />}
        </button>
      </div>
      <div className={cn("border-t border-line bg-paper px-5 py-4 lg:hidden", open ? "block" : "hidden")}>
        <nav className="flex flex-col gap-1" aria-label="Mobile">
          {links.map((link) =>
            link.href.startsWith("/#") ? (
              <a
                key={link.label}
                href={link.href}
                onClick={() => setOpen(false)}
                className="rounded-field px-3 py-2.5 text-sm text-ink hover:bg-soft"
              >
                {link.label}
              </a>
            ) : (
              <Link
                key={link.label}
                to={link.href}
                onClick={() => setOpen(false)}
                className="rounded-field px-3 py-2.5 text-sm text-ink hover:bg-soft"
              >
                {link.label}
              </Link>
            ),
          )}
          <div className="mt-3 flex gap-2 border-t border-line pt-3">
            {user ? (
              <Link to="/app" className="flex-1">
                <Button className="w-full">Open workspace</Button>
              </Link>
            ) : (
              <>
                <Link to="/login" className="flex-1">
                  <Button variant="secondary" className="w-full">
                    Sign in
                  </Button>
                </Link>
                <Link to="/signup" className="flex-1">
                  <Button className="w-full">Start free</Button>
                </Link>
              </>
            )}
          </div>
        </nav>
      </div>
    </header>
  );
}
