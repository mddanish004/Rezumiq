import { SignIn } from "@clerk/clerk-react";
import { useLocation } from "react-router-dom";
import { AuthLayout } from "./AuthLayout";

export default function LoginPage() {
  const location = useLocation();
  const redirect = (location.state as { from?: string } | null)?.from ?? "/app";

  return (
    <AuthLayout title="Welcome back" subtitle="Sign in to open your workspace.">
      <div className="[&_.cl-footerActionLink]:text-muted">
        <SignIn signUpUrl="/signup" redirectUrl={redirect} />
      </div>
    </AuthLayout>
  );
}
