import { useState } from "react";
import { Link } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { AuthLayout } from "./AuthLayout";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { api } from "@/lib/api";

const schema = z.object({ email: z.string().trim().email("Enter a valid email") });
type FormValues = z.infer<typeof schema>;

export default function ForgotPassword() {
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");
  const form = useForm<FormValues>({ resolver: zodResolver(schema), defaultValues: { email: "" } });

  const onSubmit = async (values: FormValues) => {
    setError("");
    try {
      await api.requestPasswordReset(values.email);
      setSent(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not send the email. Try again.");
    }
  };

  return (
    <AuthLayout
      title={sent ? "Check your inbox." : "Reset your password."}
      subtitle={
        sent
          ? "If an account exists for that address, a reset link is on its way. The link expires in a few hours."
          : "Enter the email on your account. We will send a reset link if it exists."
      }
      footer={
        <Link to="/login" className="font-medium text-ink underline decoration-line underline-offset-4 hover:decoration-ink">
          Back to sign in
        </Link>
      }
    >
      {sent ? (
        <div className="rounded-card border border-line bg-surface p-5 text-sm leading-6 text-muted">
          Nothing yet? Check spam, or try a different address. Delivery can take a minute.
        </div>
      ) : (
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          <Input
            label="Email"
            type="email"
            autoComplete="email"
            placeholder="you@example.com"
            error={form.formState.errors.email?.message}
            {...form.register("email")}
          />
          {error ? (
            <p role="alert" className="rounded-field border border-danger/20 bg-danger/5 px-3 py-2.5 text-sm text-danger">
              {error}
            </p>
          ) : null}
          <Button type="submit" className="w-full" size="lg" disabled={form.formState.isSubmitting}>
            {form.formState.isSubmitting ? "Sending..." : "Send reset link"}
          </Button>
        </form>
      )}
    </AuthLayout>
  );
}
