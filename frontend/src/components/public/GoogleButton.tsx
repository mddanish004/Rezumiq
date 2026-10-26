import { useEffect } from "react";
import { primeCsrf, csrfToken, api } from "@/lib/api";

export function GoogleButton({ label = "Continue with Google" }: { label?: string }) {
  useEffect(() => {
    void primeCsrf();
  }, []);

  return (
    <form action={`${api.url}/_allauth/browser/v1/auth/provider/redirect`} method="POST">
      <input type="hidden" name="provider" value="google" />
      <input
        type="hidden"
        name="callback_url"
        value={`${window.location.origin}/auth/callback?next=${encodeURIComponent("/app")}`}
      />
      <input type="hidden" name="csrfmiddlewaretoken" value={csrfToken()} />
      <button
        type="submit"
        className="focus-ring flex h-11 w-full items-center justify-center gap-2.5 rounded-field border border-line bg-surface text-sm font-medium text-ink transition-colors hover:bg-paper"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" aria-hidden="true">
          <path fill="#4285F4" d="M21.6 12.23c0-.71-.06-1.4-.18-2.05H12v3.87h5.38a4.6 4.6 0 0 1-2 3.02v2.51h3.24c1.9-1.75 2.98-4.33 2.98-7.35Z" />
          <path fill="#34A853" d="M12 22c2.7 0 4.96-.9 6.62-2.42l-3.24-2.51c-.9.6-2.04.96-3.38.96-2.6 0-4.8-1.76-5.59-4.12H3.06v2.6A10 10 0 0 0 12 22Z" />
          <path fill="#FBBC05" d="M6.41 13.9a6 6 0 0 1 0-3.8V7.5H3.06a10 10 0 0 0 0 9l3.35-2.6Z" />
          <path fill="#EA4335" d="M12 6.04c1.47 0 2.79.5 3.83 1.5l2.87-2.87A9.6 9.6 0 0 0 12 2a10 10 0 0 0-8.94 5.5l3.35 2.6C7.2 7.8 9.4 6.04 12 6.04Z" />
        </svg>
        {label}
      </button>
    </form>
  );
}
