import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, Download, KeyRound, LogOut, ShieldAlert, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { api, ApiError, type AiKey, type Me } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { formatDate } from "@/lib/utils";

const PROVIDERS = [
  { id: "groq", label: "Groq", hint: "Default. Fast, low cost." },
  { id: "openai", label: "OpenAI", hint: "GPT models." },
  { id: "anthropic", label: "Anthropic", hint: "Claude models." },
  { id: "openrouter", label: "OpenRouter", hint: "Many providers behind one key." },
] as const;

export default function Settings() {
  const { user, logout } = useAuth();
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [name, setName] = useState(user?.name ?? "");
  const [username, setUsername] = useState(user?.username ?? "");
  const [checkedUsername, setCheckedUsername] = useState<string | null>(null);
  const [keyProvider, setKeyProvider] = useState<string>("groq");
  const [apiKey, setApiKey] = useState("");
  const [modelId, setModelId] = useState("");
  const keys = useQuery<AiKey[]>({ queryKey: ["ai-keys"], queryFn: api.aiKeys, retry: false });

  useEffect(() => {
    setName(user?.name ?? "");
    setUsername(user?.username ?? "");
  }, [user?.name, user?.username]);

  const usernameCheck = useQuery({
    queryKey: ["username-check", username],
    queryFn: () => api.usernameAvailable(username),
    enabled: false,
  });

  const saveAccount = useMutation({
    mutationFn: () => {
      const body: { name?: string; username?: string } = {};
      if (name.trim() !== (user?.name ?? "")) body.name = name.trim();
      if (username.trim().toLowerCase() !== (user?.username ?? "")) body.username = username.trim().toLowerCase();
      return api.updateMe(body);
    },
    onSuccess: async (updated: Me) => {
      queryClient.setQueryData(["me"], updated);
      await queryClient.invalidateQueries({ queryKey: ["username-check"] });
      toast.success("Account updated");
    },
    onError: (error) => {
      if (error instanceof ApiError && error.status === 409) {
        toast.error("That username is not available yet. Names can be changed on a cooldown.");
      } else {
        toast.error(error.message);
      }
    },
  });

  const putKey = useMutation({
    mutationFn: () => api.putAiKey(keyProvider, apiKey.trim(), modelId.trim() || undefined),
    onSuccess: async (key) => {
      setApiKey("");
      setModelId("");
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["ai-keys"] }),
        queryClient.invalidateQueries({ queryKey: ["usage"] }),
        queryClient.invalidateQueries({ queryKey: ["me"] }),
      ]);
      toast.success(`${key.provider} key verified and saved`);
    },
    onError: (error) => toast.error(error.message),
  });

  const toggleKey = useMutation({
    mutationFn: ({ provider, enabled }: { provider: string; enabled: boolean }) =>
      api.updateAiKey(provider, { enabled }),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["ai-keys"] }),
        queryClient.invalidateQueries({ queryKey: ["usage"] }),
      ]);
    },
    onError: (error) => toast.error(error.message),
  });

  const removeKey = useMutation({
    mutationFn: (provider: string) => api.deleteAiKey(provider),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["ai-keys"] }),
        queryClient.invalidateQueries({ queryKey: ["usage"] }),
      ]);
      toast.success("AI key removed");
    },
    onError: (error) => toast.error(error.message),
  });

  const removeAccount = useMutation({
    mutationFn: api.deleteMe,
    onSuccess: async () => {
      await logout();
      navigate("/");
    },
    onError: (error) => toast.error(error.message),
  });

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Preferences / Settings"
        title="Account and keys."
        description="Your account, your AI provider, and the data controls. Nothing here is shared publicly."
      />

      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="p-5">
          <p className="eyebrow">Account</p>
          <form
            className="mt-4 space-y-4"
            onSubmit={(event) => {
              event.preventDefault();
              saveAccount.mutate();
            }}
          >
            <Input label="Name" value={name} onChange={(event) => setName(event.target.value)} />
            <div>
              <div className="flex items-end gap-2">
                <div className="flex-1">
                  <Input
                    label="Username"
                    value={username}
                    onChange={(event) => {
                      setUsername(event.target.value.toLowerCase());
                      setCheckedUsername(null);
                    }}
                    hint="Used in public profile and share links."
                  />
                </div>
                <Button
                  variant="secondary"
                  size="sm"
                  className="mb-5"
                  onClick={async () => {
                    const result = await usernameCheck.refetch();
                    setCheckedUsername(result.data?.username ?? username);
                    toast[result.data?.available ? "success" : "error"](
                      result.data?.available ? "Username is available" : "Username is taken or reserved",
                    );
                  }}
                >
                  Check
                </Button>
              </div>
              {checkedUsername && checkedUsername === username && usernameCheck.data ? (
                <p className={`text-xs ${usernameCheck.data.available ? "text-success" : "text-danger"}`}>
                  {usernameCheck.data.available ? "Available" : "Not available"}
                </p>
              ) : null}
            </div>
            <div className="flex items-center justify-between rounded-field border border-line bg-paper/60 px-3 py-2.5 text-xs">
              <span className="text-muted">Email</span>
              <span className="flex items-center gap-2">
                {user?.email}
                <Badge tone={user?.emailVerified ? "success" : "warning"}>
                  {user?.emailVerified ? "Verified" : "Unverified"}
                </Badge>
              </span>
            </div>
            <Button type="submit" size="sm" disabled={saveAccount.isPending}>
              {saveAccount.isPending ? "Saving..." : "Save changes"}
            </Button>
          </form>
        </Card>

        <Card className="p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="eyebrow">AI keys</p>
              <p className="mt-1 text-sm text-muted">
                Encrypted at rest. A key bypasses monthly AI limits. AI review still needs a paid plan.
              </p>
            </div>
            <KeyRound size={18} className="text-muted" />
          </div>
          <div className="mt-4 space-y-2">
            {(keys.data ?? []).map((key) => (
              <div key={key.provider} className="flex flex-wrap items-center justify-between gap-2 rounded-field border border-line bg-paper/60 px-3 py-2.5">
                <div>
                  <p className="text-sm font-medium capitalize">{key.provider}</p>
                  <p className="text-[11px] text-muted">
                    ····{key.keyHint} · verified {formatDate(key.verifiedAt)}
                    {key.modelId ? ` · ${key.modelId}` : ""}
                  </p>
                </div>
                <div className="flex items-center gap-1.5">
                  <Badge tone={key.enabled ? "success" : "outline"}>{key.enabled ? "Active" : "Off"}</Badge>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => toggleKey.mutate({ provider: key.provider, enabled: !key.enabled })}
                  >
                    {key.enabled ? "Disable" : "Enable"}
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => removeKey.mutate(key.provider)} aria-label="Delete key">
                    <Trash2 size={13} />
                  </Button>
                </div>
              </div>
            ))}
            {(keys.data ?? []).length === 0 ? (
              <p className="rounded-field border border-dashed border-line p-3 text-xs text-muted">
                No AI key saved yet. Add one below to stop using the plan limits.
              </p>
            ) : null}
          </div>
          <form
            className="mt-4 space-y-3 border-t border-line pt-4"
            onSubmit={(event) => {
              event.preventDefault();
              if (apiKey.trim().length >= 10) putKey.mutate();
            }}
          >
            <label className="block">
              <span className="mb-1.5 block font-mono text-[10px] uppercase tracking-[0.16em] text-muted">Provider</span>
              <select
                value={keyProvider}
                onChange={(event) => setKeyProvider(event.target.value)}
                className="focus-ring h-10 w-full rounded-field border border-line bg-paper px-3 text-sm"
              >
                {PROVIDERS.map((provider) => (
                  <option key={provider.id} value={provider.id}>
                    {provider.label}
                  </option>
                ))}
              </select>
            </label>
            <Input
              label="API key"
              type="password"
              value={apiKey}
              onChange={(event) => setApiKey(event.target.value)}
              placeholder="Paste the provider key"
              hint="Verified with a tiny request before it is saved."
            />
            <Input
              label="Model (optional)"
              value={modelId}
              onChange={(event) => setModelId(event.target.value)}
              placeholder="Leave blank for the provider default"
            />
            <Button type="submit" size="sm" disabled={apiKey.trim().length < 10 || putKey.isPending}>
              {putKey.isPending ? "Verifying..." : "Save AI key"}
            </Button>
          </form>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="p-5">
          <p className="eyebrow">Your data</p>
          <p className="mt-2 text-sm leading-6 text-muted">
            Download a JSON copy of your account, profile, resumes, versions, jobs, share links, and AI
            usage. The export does not include prompts or outputs.
          </p>
          <a href={api.dataExportUrl()} target="_blank" rel="noreferrer">
            <Button variant="secondary" size="sm" className="mt-4">
              <Download size={14} /> Download JSON
            </Button>
          </a>
          <div className="mt-4 flex items-center gap-3 border-t border-line pt-4">
            <Button
              variant="secondary"
              size="sm"
              onClick={async () => {
                await logout();
                navigate("/");
              }}
            >
              <LogOut size={14} /> Sign out
            </Button>
            <span className="text-[11px] text-muted">Session ends on this device.</span>
          </div>
        </Card>

        <Card className="border-danger/20 p-5">
          <p className="eyebrow text-danger">Danger zone</p>
          <p className="mt-2 flex items-center gap-2 text-sm font-medium text-danger">
            <ShieldAlert size={15} /> Delete account
          </p>
          <p className="mt-2 text-sm leading-6 text-muted">
            This removes your profile, resumes, versions, jobs, share links, and AI keys. Billing records
            required by law are retained. There is no undo.
          </p>
          <Button
            variant="danger"
            size="sm"
            className="mt-4"
            disabled={removeAccount.isPending}
            onClick={() => {
              const typed = window.prompt(`Type your username (${user?.username}) to delete the account.`);
              if (typed === user?.username) removeAccount.mutate();
            }}
          >
            {removeAccount.isPending ? "Deleting..." : "Delete my account"}
          </Button>
        </Card>
      </div>

      {keys.isError ? (
        <p className="text-xs text-danger">AI keys could not be loaded. Refresh to try again.</p>
      ) : null}
      <p className="flex items-center gap-1.5 text-[11px] text-muted">
        <Check size={12} className="text-forest" /> Account changes are applied immediately. Username
        changes have a cooldown.
      </p>
    </div>
  );
}
