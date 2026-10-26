import { useState } from "react";
import { Link, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Eye, EyeOff } from "lucide-react";
import { AuthLayout } from "./AuthLayout";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { GoogleButton } from "@/components/public/GoogleButton";
import { useAuth } from "@/lib/auth";
import { ApiError } from "@/lib/api";

const schema = z.object({
  email: z.string().trim().email("Enter a valid email"),
  password: z.string().min(1, "Enter your password"),
});

type FormValues = z.infer<typeof schema>;

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [params] = useSearchParams();
  const providerError = params.has("error");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const form = useForm<FormValues>({ resolver: zodResolver(schema), defaultValues: { email: "", password: "" } });

  const onSubmit = async (values: FormValues) => {
    setError("");
    try {
      await login(values.email, values.password);
      const from = (location.state as { from?: string } | null)?.from ?? "/app";
      navigate(from, { replace: true });
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setError("That email and password do not match. Check both and try again.");
      } else if (err instanceof ApiError && err.status === 403) {
        setError("This account is suspended. Contact support if you think that is a mistake.");
      } else {
        setError(err instanceof Error ? err.message : "Could not sign in. Try again.");
      }
    }
  };

  return (
    <AuthLayout
      title="Welcome back."
      subtitle="Sign in to your workspace. Your drafts, versions, and share links are where you left them."
      footer={
        <>
          New here?{" "}
          <Link to="/signup" className="font-medium text-ink underline decoration-line underline-offset-4 hover:decoration-ink">
            Create an account
          </Link>
        </>
      }
    >
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
        {providerError ? (
          <p className="rounded-field border border-line bg-surface px-3 py-2.5 text-sm leading-6 text-muted">
            Google sign-in did not finish. Try again, or use your email and password.
          </p>
        ) : null}
        <Input
          label="Email"
          type="email"
          autoComplete="email"
          placeholder="you@example.com"
          error={form.formState.errors.email?.message}
          {...form.register("email")}
        />
        <Input
          label="Password"
          type={showPassword ? "text" : "password"}
          autoComplete="current-password"
          placeholder="Your password"
          error={form.formState.errors.password?.message}
          trailing={
            <button
              type="button"
              onClick={() => setShowPassword((value) => !value)}
              className="text-muted transition-colors hover:text-ink"
              aria-label={showPassword ? "Hide password" : "Show password"}
            >
              {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          }
          {...form.register("password")}
        />
        <div className="flex items-center justify-between">
          <Link to="/forgot-password" className="text-xs text-muted underline decoration-line underline-offset-4 hover:text-ink">
            Forgot password?
          </Link>
        </div>
        {error ? (
          <p role="alert" className="rounded-field border border-danger/20 bg-danger/5 px-3 py-2.5 text-sm text-danger">
            {error}
          </p>
        ) : null}
        <Button type="submit" className="w-full" size="lg" disabled={form.formState.isSubmitting}>
          {form.formState.isSubmitting ? "Signing in..." : "Sign in"}
        </Button>
      </form>
      <div className="my-6 flex items-center gap-3">
        <span className="h-px flex-1 bg-line" />
        <span className="font-mono text-[9px] uppercase tracking-[0.14em] text-muted">or</span>
        <span className="h-px flex-1 bg-line" />
      </div>
      <GoogleButton />
    </AuthLayout>
  );
}
