import { Link } from "react-router-dom";
import { Logo } from "@/components/ui/Logo";

export function PublicFooter() {
  return (
    <footer className="border-t border-line bg-paper">
      <div className="mx-auto grid max-w-[1240px] gap-10 px-5 py-12 md:grid-cols-[1.4fr_1fr_1fr_1fr] lg:px-8">
        <div>
          <Logo />
          <p className="mt-4 max-w-xs text-sm leading-6 text-muted">
            An editorial resume studio for people who care how their work reads. Form or LaTeX, scored
            against real ATS parsers.
          </p>
          <p className="mt-6 font-mono text-[10px] uppercase tracking-[0.16em] text-muted">
            Made for every field, not just software.
          </p>
        </div>
        <FooterColumn
          title="Product"
          links={[
            { label: "Features", to: "/#features" },
            { label: "Templates", to: "/#templates" },
            { label: "ATS Checker", to: "/ats-checker" },
            { label: "Pricing", to: "/#pricing" },
          ]}
        />
        <FooterColumn
          title="Account"
          links={[
            { label: "Sign in", to: "/login" },
            { label: "Create account", to: "/signup" },
          ]}
        />
        <FooterColumn
          title="Legal"
          links={[
            { label: "Privacy", to: "/legal/privacy" },
            { label: "Terms", to: "/legal/terms" },
            { label: "Refunds", to: "/legal/refunds" },
          ]}
        />
      </div>
      <div className="border-t border-line">
        <div className="mx-auto flex max-w-[1240px] flex-col gap-2 px-5 py-5 text-xs text-muted md:flex-row md:items-center md:justify-between lg:px-8">
          <p>© {new Date().getFullYear()} Rezumiq. All rights reserved.</p>
          <p className="font-mono text-[10px] uppercase tracking-[0.14em]">
            Real LaTeX PDFs · No interviews promised
          </p>
        </div>
      </div>
    </footer>
  );
}

function FooterColumn({ title, links }: { title: string; links: Array<{ label: string; to: string }> }) {
  return (
    <div>
      <p className="eyebrow">{title}</p>
      <ul className="mt-4 space-y-2.5">
        {links.map((link) =>
          link.to.startsWith("/#") ? (
            <li key={link.label}>
              <a href={link.to} className="text-sm text-muted transition-colors hover:text-ink">
                {link.label}
              </a>
            </li>
          ) : (
            <li key={link.label}>
              <Link to={link.to} className="text-sm text-muted transition-colors hover:text-ink">
                {link.label}
              </Link>
            </li>
          ),
        )}
      </ul>
    </div>
  );
}
