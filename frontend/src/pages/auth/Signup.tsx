import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
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

const schema = z
  .object({
    name: z.string().trim().min(2, "Enter your full name"),
    email: z.string().trim().email("Enter a valid email"),
    password: z.string().min(8, "Use at least 8 characters"),
    confirm: z.string(),
  })
  .refine((values) => values.password === values.confirm, {
    path: ["confirm"],
    message: "Passwords do not match",
  });

type FormValues = z.infer<typeof schema>;

export default function Signup() {
  const { signup } = useAuth();
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { name: "", email: "", password: "", confirm: "" },
  });

  const onSubmit = async (values: FormValues) => {
    setError("");
    try {
      await signup(values.email, values.password, values.name);
      navigate("/app", { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create the account. Try again.");
      if (err instanceof ApiError && err.status === 401) {
        setError("Check your inbox to verify the email, then sign in.");
      }
    }
  };

  return (
    <AuthLayout
      title="Start with a real draft."
      subtitle="One free AI-written resume, ATS checks, and a LaTeX PDF. No card required."
      footer={
        <>
          Already have an account?{" "}
          <Link to="/login" className="font-medium text-ink underline decoration-line underline-offset-4 hover:decoration-ink">
            Sign in
          </Link>
        </>
      }
    >
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
        <Input
          label="Full name"
          autoComplete="name"
          placeholder="Rohan Kulkarni"
          error={form.formState.errors.name?.message}
          {...form.register("name")}
        />
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
          autoComplete="new-password"
          placeholder="At least 8 characters"
          hint="Use a passphrase you will remember. Avoid reuse."
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
        <Input
          label="Confirm password"
          type={showPassword ? "text" : "password"}
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
        <Button type="submit" className="w-full" size="lg" disabled={form.formState.isSubmitting}>
          {form.formState.isSubmitting ? "Creating account..." : "Create free account"}
        </Button>
        <p className="text-center text-[11px] leading-5 text-muted">
          By continuing you agree to the{" "}
          <Link to="/legal/terms" className="underline decoration-line underline-offset-2 hover:text-ink">
            terms
          </Link>{" "}
          and{" "}
          <Link to="/legal/privacy" className="underline decoration-line underline-offset-2 hover:text-ink">
            privacy policy
          </Link>
          .
        </p>
      </form>
      <div className="my-6 flex items-center gap-3">
        <span className="h-px flex-1 bg-line" />
        <span className="font-mono text-[9px] uppercase tracking-[0.14em] text-muted">or</span>
        <span className="h-px flex-1 bg-line" />
      </div>
      <GoogleButton label="Sign up with Google" />
    </AuthLayout>
  );
}
