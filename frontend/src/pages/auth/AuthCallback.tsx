import { useEffect } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "@/lib/auth";
import { Spinner } from "@/components/ui/Spinner";

export default function AuthCallback() {
  const { user, loading } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const error = params.get("error");

  useEffect(() => {
    if (loading) return;
    if (user) {
      const next = params.get("next") ?? "/app";
      navigate(next, { replace: true });
    }
  }, [loading, user, navigate, params]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-paper px-6">
      <div className="w-full max-w-sm text-center">
        {error ? (
          <>
            <p className="font-display text-2xl">Google sign-in did not finish.</p>
            <p className="mt-2 text-sm leading-6 text-muted">
              Try again, or use your email and password. The provider returned: {error}
            </p>
            <Link to="/login" className="mt-6 inline-block text-sm font-medium underline decoration-line underline-offset-4">
              Back to sign in
            </Link>
          </>
        ) : (
          <>
            <Spinner className="justify-center" label="Finishing sign-in" />
            {!loading && !user ? (
              <p className="mt-4 text-sm text-muted">
                The session did not stick.{" "}
                <Link to="/login" className="underline decoration-line underline-offset-2">
                  Try signing in again
                </Link>
                .
              </p>
            ) : null}
          </>
        )}
      </div>
    </div>
  );
}
