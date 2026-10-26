import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { AuthLayout } from "./AuthLayout";
import { Spinner } from "@/components/ui/Spinner";
import { api } from "@/lib/api";

type Status = "working" | "success" | "error";

export default function VerifyEmail() {
  const { key = "" } = useParams();
  const [status, setStatus] = useState<Status>("working");
  const [error, setError] = useState("");
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    if (!key) {
      setStatus("error");
      setError("This verification link is missing its key.");
      return;
    }
    api
      .verifyEmail(key)
      .then(() => setStatus("success"))
      .catch((err: unknown) => {
        setStatus("error");
        setError(err instanceof Error ? err.message : "Could not verify this email.");
      });
  }, [key]);

  return (
    <AuthLayout
      title={status === "success" ? "Email verified." : status === "error" ? "That link did not work." : "Verifying your email."}
      subtitle={
        status === "success"
          ? "Your address is confirmed. Sign in to get back to your workspace."
          : status === "error"
            ? "The link may have expired or already been used."
            : "One moment while we confirm the address on your account."
      }
      footer={
        <Link to="/login" className="font-medium text-ink underline decoration-line underline-offset-4 hover:decoration-ink">
          Go to sign in
        </Link>
      }
    >
      {status === "working" ? <Spinner label="Verifying" /> : null}
      {status === "success" ? (
        <div className="rounded-card border border-line bg-surface p-5 text-sm leading-6 text-muted">
          The address on your account is now verified.
        </div>
      ) : null}
      {status === "error" ? (
        <p role="alert" className="rounded-field border border-danger/20 bg-danger/5 px-3 py-2.5 text-sm text-danger">
          {error}
        </p>
      ) : null}
    </AuthLayout>
  );
}
