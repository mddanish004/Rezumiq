import { PublicHeader } from "@/components/public/PublicHeader";
import { PublicFooter } from "@/components/public/PublicFooter";
import { useParams } from "react-router-dom";

const COPY: Record<string, { title: string; body: string[] }> = {
  privacy: {
    title: "Privacy policy",
    body: [
      "This page is a placeholder while the production policy is reviewed. The short version: resumes and profile content belong to you, are never sold, and are sent to an AI provider only when you ask for an AI action.",
      "Sensitive fields marked in the editor are masked before a prompt leaves the server. Share links are public only when you create them, and unlisted links are marked noindex.",
      "You can export your data as JSON or delete your account from Settings. Some billing records are retained where required by law.",
    ],
  },
  terms: {
    title: "Terms of service",
    body: [
      "This page is a placeholder while the production terms are reviewed. Rezumiq provides resume editing, scoring, AI suggestions, and hosting for share links.",
      "AI output can be wrong. Review every suggestion before you apply it, and never treat a score as a promise of an interview or an offer.",
      "You are responsible for the accuracy of the facts in your resume and for the content you publish through a share link.",
    ],
  },
  refunds: {
    title: "Refund policy",
    body: [
      "Self-serve refunds are available once per account, within six hours of a successful payment. The refund returns the amount captured, excluding any provider fee where one applies.",
      "Refunds are meant for trying a plan, not for using the full allowance. Accounts that have used more than three AI tailors or three AI-written resumes since paying are not eligible for a self-serve refund.",
      "Paid subscriptions are cancelled through the billing provider. Cancelling stops the next renewal; access continues to the end of the current period.",
    ],
  },
};

export default function Legal() {
  const { page = "privacy" } = useParams();
  const content = COPY[page] ?? COPY.privacy;
  return (
    <div className="min-h-screen bg-paper">
      <PublicHeader />
      <main className="mx-auto max-w-3xl px-5 py-16 lg:py-24">
        <p className="eyebrow">Legal / Placeholder</p>
        <h1 className="mt-3 font-display text-4xl tracking-[-0.02em]">{content.title}</h1>
        <div className="mt-8 space-y-4 border-t border-line pt-8 text-sm leading-7 text-muted">
          {content.body.map((paragraph) => (
            <p key={paragraph}>{paragraph}</p>
          ))}
        </div>
      </main>
      <PublicFooter />
    </div>
  );
}
