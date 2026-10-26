import { createContext, useContext, type ReactNode } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Navigate, useLocation } from "react-router-dom";
import { api, ApiError, type Me } from "./api";
import { Spinner } from "@/components/ui/Spinner";

type AuthContextValue = {
  user: Me | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, name?: string) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const meQuery = useQuery<Me | null>({
    queryKey: ["me"],
    queryFn: async () => {
      try {
        return await api.me();
      } catch (error) {
        if (error instanceof ApiError && error.status === 401) return null;
        throw error;
      }
    },
    retry: false,
    staleTime: 60_000,
  });

  const loginMutation = useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) => api.login(email, password),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["me"] });
    },
  });

  const signupMutation = useMutation({
    mutationFn: async ({ email, password, name }: { email: string; password: string; name?: string }) => {
      await api.signup(email, password);
      if (name?.trim()) await api.updateMe({ name: name.trim() });
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["me"] });
    },
  });

  const logout = async () => {
    await api.logout();
    queryClient.setQueryData(["me"], null);
    queryClient.clear();
  };

  return (
    <AuthContext.Provider
      value={{
        user: meQuery.data ?? null,
        loading: meQuery.isLoading,
        login: async (email, password) => {
          await loginMutation.mutateAsync({ email, password });
        },
        signup: async (email, password, name) => {
          await signupMutation.mutateAsync({ email, password, name });
        },
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
}

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-paper">
        <Spinner label="Opening your workspace" />
      </div>
    );
  }
  if (!user) return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  return <>{children}</>;
}

export function AdminRoute({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-paper">
        <Spinner label="Checking access" />
      </div>
    );
  }
  if (!user?.isAdmin) return <Navigate to="/app" replace />;
  return <>{children}</>;
}
