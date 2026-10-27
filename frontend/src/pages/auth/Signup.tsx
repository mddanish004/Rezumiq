import { SignUp } from "@clerk/clerk-react";
import { AuthLayout } from "./AuthLayout";

export default function SignupPage() {
  return (
    <AuthLayout title="Create your account" subtitle="Start with a free plan. No card needed.">
      <div className="[&_.cl-footerActionLink]:text-muted">
        <SignUp signInUrl="/login" redirectUrl="/app" />
      </div>
    </AuthLayout>
  );
}
