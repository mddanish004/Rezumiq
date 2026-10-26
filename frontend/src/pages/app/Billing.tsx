import { useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, CreditCard, ReceiptText } from "lucide-react";
import { toast } from "sonner";
import { api, type Counter, type RefundQuote, type Subscription, type Usage } from "@/lib/api";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { formatDate, inr } from "@/lib/utils";

const plans = [
  {
    id: "free" as const,
    name: "Free",
    price: "₹0",
    cadence: "forever",
    body: "One real draft, ATS checks, and LaTeX export.",
    features: ["1 AI-written resume", "1 tailor / month", "50 AI edits", "20 ATS checks"],
  },
  {
    id: "season_pass" as const,
    name: "Season Pass",
    price: "₹499",
    cadence: "one-time / 6 months",
    body: "A focused season of applications without a subscription.",
    features: ["40 AI tailors", "1,000 AI edits", "30 AI drafts", "200 ATS checks", "100 AI reviews"],
  },
  {
    id: "pro" as const,
    name: "Pro",
    price: "₹129",
    cadence: "per month",
    body: "For a career that keeps moving. Cancel anytime.",
    features: ["60 AI tailors", "1,000 AI edits", "30 AI drafts", "200 ATS checks", "100 AI reviews"],
  },
];

export default function Billing() {
  const subscription = useQuery<Subscription>({ queryKey: ["subscription"], queryFn: api.subscription });
  const usage = useQuery<Usage>({ queryKey: ["usage"], queryFn: api.usage });
  const quote = useQuery<RefundQuote>({ queryKey: ["refund-quote"], queryFn: api.refundQuote, retry: false });
  const queryClient = useQueryClient();
  const [promo, setPromo] = useState("");
  const current = subscription.data?.plan ?? usage.data?.plan ?? "free";
  const active = subscription.data?.subscription;

  const checkout = useMutation({
    mutationFn: (plan: "season_pass" | "pro") => api.createCheckout(plan),
    onSuccess: (data) => {
      window.location.assign(data.checkoutUrl);
    },
    onError: (error) => toast.error(error.message),
  });

  const cancel = useMutation({
    mutationFn: api.cancelSubscription,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["subscription"] });
      toast.success("Pro will stop at the end of the period");
    },
    onError: (error) => toast.error(error.message),
  });

  const refund = useMutation({
    mutationFn: (paymentId: string) => api.requestRefund(paymentId),
    onSuccess: async (data) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["subscription"] }),
        queryClient.invalidateQueries({ queryKey: ["usage"] }),
        queryClient.invalidateQueries({ queryKey: ["refund-quote"] }),
      ]);
      toast.success(`Refund requested for ${inr(data.refundPaise)}. It can take a few days to settle.`);
    },
    onError: (error) => toast.error(error.message),
  });

  const redeem = useMutation({
    mutationFn: () => api.redeemPromo(promo.trim()),
    onSuccess: async (data) => {
      setPromo("");
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["subscription"] }),
        queryClient.invalidateQueries({ queryKey: ["me"] }),
        queryClient.invalidateQueries({ queryKey: ["usage"] }),
      ]);
      toast.success(`${data.plan === "pro" ? "Pro" : "Season Pass"} applied`);
    },
    onError: (error) => toast.error(error.message),
  });

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Preferences / Billing"
        title="One plan, spelled out."
        description="Every AI limit is visible before you pay. Prices exclude taxes; the hosted checkout shows the final amount."
      />

      <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
        <Card className="p-5">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="eyebrow">Current plan</p>
              <p className="mt-2 font-display text-3xl">
                {current === "season_pass" ? "Season Pass" : current === "pro" ? "Pro" : "Free"}
              </p>
              <p className="mt-1 text-sm text-muted">
                {active
                  ? `${active.status === "cancelled" ? "Access ends" : "Renews"} ${formatDate(active.currentPeriodEnd)}`
                  : "No active subscription. The free tier is always available."}
              </p>
            </div>
            {current !== "free" ? <Badge tone="success">Active</Badge> : <Badge tone="outline">Free tier</Badge>}
          </div>
          <div className="mt-5 grid grid-cols-2 gap-3 border-t border-line pt-4 sm:grid-cols-4">
            {(
              [
                ["Tailors", usage.data?.tailor],
                ["ATS checks", usage.data?.ats],
                ["Edits", usage.data?.edit],
                ["Reviews", usage.data?.review],
              ] as Array<[string, Counter | undefined]>
            ).map(([label, counter]) => (
              <div key={label}>
                <p className="font-mono text-[9px] uppercase tracking-[0.1em] text-muted">{label}</p>
                <p className="mt-1 text-sm">{counter ? `${counter.used} / ${counter.limit}` : "-"}</p>
              </div>
            ))}
          </div>
          {current === "pro" && active?.status === "active" ? (
            <Button
              variant="secondary"
              size="sm"
              className="mt-4"
              disabled={cancel.isPending}
              onClick={() => {
                if (window.confirm("Cancel Pro at the end of the current period?")) cancel.mutate();
              }}
            >
              Cancel Pro
            </Button>
          ) : null}
        </Card>

        <Card className="p-5">
          <p className="eyebrow">Redeem a code</p>
          <p className="mt-2 text-sm text-muted">Promo and ambassador codes extend a plan immediately.</p>
          <form
            className="mt-3 flex gap-2"
            onSubmit={(event) => {
              event.preventDefault();
              if (promo.trim()) redeem.mutate();
            }}
          >
            <input
              value={promo}
              onChange={(event) => setPromo(event.target.value.toUpperCase())}
              placeholder="SEASON26"
              className="focus-ring h-10 flex-1 rounded-field border border-line bg-paper px-3 font-mono text-xs uppercase tracking-[0.1em]"
            />
            <Button type="submit" disabled={!promo.trim() || redeem.isPending}>
              {redeem.isPending ? "Checking..." : "Apply"}
            </Button>
          </form>
          <p className="mt-3 flex items-center gap-1.5 text-[11px] text-muted">
            <ReceiptText size={12} /> One redemption per code.
          </p>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        {plans.map((plan) => (
          <Card
            key={plan.id}
            className={`flex flex-col p-5 ${current === plan.id ? "border-ink" : ""}`}
          >
            <div className="flex items-center justify-between">
              <p className="font-mono text-[10px] uppercase tracking-[0.14em] text-muted">{plan.name}</p>
              {current === plan.id ? <Badge tone="lime">Current</Badge> : null}
            </div>
            <div className="mt-3 flex items-end gap-2">
              <span className="font-display text-3xl">{plan.price}</span>
              <span className="pb-1 text-[11px] text-muted">{plan.cadence}</span>
            </div>
            <p className="mt-2 text-xs leading-5 text-muted">{plan.body}</p>
            <ul className="mt-4 flex-1 space-y-2">
              {plan.features.map((feature) => (
                <li key={feature} className="flex items-center gap-2 text-xs">
                  <Check size={12} className="text-forest" strokeWidth={3} />
                  {feature}
                </li>
              ))}
            </ul>
            <div className="mt-5">
              {plan.id === "free" ? (
                <Link to="/app/resumes">
                  <Button variant="secondary" size="sm" className="w-full">
                    Keep using free
                  </Button>
                </Link>
              ) : (
                <Button
                  size="sm"
                  className="w-full"
                  variant={plan.id === "season_pass" ? "primary" : "secondary"}
                  disabled={checkout.isPending || current === plan.id}
                  onClick={() => checkout.mutate(plan.id)}
                >
                  <CreditCard size={13} />
                  {current === plan.id ? "Current plan" : plan.id === "season_pass" ? "Buy Season Pass" : "Subscribe to Pro"}
                </Button>
              )}
            </div>
          </Card>
        ))}
      </div>

      <Card className="p-5">
        <p className="eyebrow">Refunds</p>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">
          Self-serve refunds are available once per account, within six hours of a successful payment.
          They are for trying a plan, not for using the full allowance.
        </p>
        {quote.isLoading ? (
          <p className="mt-4 text-sm text-muted">Checking for a refundable payment...</p>
        ) : quote.data?.quote ? (
          <div className="mt-4 flex flex-wrap items-center justify-between gap-4 rounded-field border border-line bg-paper/70 p-4">
            <div>
              <p className="text-sm font-medium">
                Refund {inr(quote.data.quote.refundPaise)} of {inr(quote.data.quote.amountPaidPaise)}
              </p>
              <p className="text-xs text-muted">
                Fee {inr(quote.data.quote.feePaise)} · available until {formatDate(quote.data.quote.refundableUntil)}
              </p>
            </div>
            <Button
              size="sm"
              variant="secondary"
              disabled={refund.isPending}
              onClick={() => {
                if (!quote.data?.quote) return;
                if (window.confirm(`Refund ${inr(quote.data.quote.refundPaise)}? The plan ends immediately.`)) {
                  refund.mutate(quote.data.quote.paymentId);
                }
              }}
            >
              {refund.isPending ? "Requesting..." : "Request refund"}
            </Button>
          </div>
        ) : quote.data?.reason ? (
          <p className="mt-4 rounded-field border border-warning/20 bg-warning/5 px-3 py-2.5 text-sm text-warning">
            {quote.data.reason}
          </p>
        ) : (
          <p className="mt-4 text-xs text-muted">
            No refundable payment is available right now. Payments become refundable only after they are
            captured, and the window closes after six hours.
          </p>
        )}
      </Card>
    </div>
  );
}
