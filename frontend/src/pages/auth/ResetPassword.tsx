import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { AuthLayout } from "./AuthLayout";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { api } from "@/lib/api";

const schema = z
  .object({
    password: z.string().min(8, "Use at least 8 characters"),
    confirm: z.string(),
  })
  .refine((values) => values.password === values.confirm, {
    path: ["confirm"],
    message: "Passwords do not match",
  });

type FormValues = z.infer<typeof schema>;

export default function ResetPassword() {
  const { key = "" } = useParams();
  const [done, setDone] = useState(false);
  const [error, setError] = useState(key ? "" : "This reset link is missing its key.");
  const form = useForm<FormValues>({ resolver: zodResolver(schema), defaultValues: { password: "", confirm: "" } });

  const onSubmit = async (values: FormValues) => {
    setError("");
    try {
      await api.resetPassword(key, values.password);
      setDone(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not reset the password. Try again.");
    }
  };

  return (
    <AuthLayout
      title={done ? "Password updated." : "Set a new password."}
      subtitle={
        done
          ? "Sign in with the new password to get back to your workspace."
          : "Choose a new password for your account. The link works once and expires in a few hours."
      }
      footer={
        <Link to="/login" className="font-medium text-ink underline decoration-line underline-offset-4 hover:decoration-ink">
          Go to sign in
        </Link>
      }
    >
      {done ? (
        <div className="rounded-card border border-line bg-surface p-5 text-sm leading-6 text-muted">
          Your password is changed. You can sign in now.
        </div>
      ) : (
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          <Input
            label="New password"
            type="password"
            autoComplete="new-password"
            placeholder="At least 8 characters"
            error={form.formState.errors.password?.message}
            {...form.register("password")}
          />
          <Input
            label="Confirm password"
            type="password"
            autoComplete="new-password"
            placeholder="Repeat the password"
            error={form.formState.errors.confirm?.message}
            {...form.register("confirm")}
          />
          {error ? (
            <p role="alert" className="rounded-field border border-danger/20 bg-danger/5 px-3 py-2.5 text-sm text-danger">
              {error}
            </p>
          ) : null}
          <Button
            type="submit"
            className="w-full"
            size="lg"
            disabled={!key || form.formState.isSubmitting}
          >
            {form.formState.isSubmitting ? "Saving..." : "Set new password"}
          </Button>
        </form>
      )}
    </AuthLayout>
  );
}
