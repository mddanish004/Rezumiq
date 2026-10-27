import { createContext, useContext, useEffect, type ReactNode } from "react";
import { useAuth as useClerkAuth } from "@clerk/clerk-react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Navigate, useLocation } from "react-router-dom";
import { api, ApiError, primeCsrf, setTokenGetter, type Me } from "./api";
import { Spinner } from "@/components/ui/Spinner";

type AuthContextValue = {
  user: Me | null;
  loading: boolean;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const { isLoaded, isSignedIn, getToken, signOut } = useClerkAuth();

  useEffect(() => {
    setTokenGetter(getToken);
  }, [getToken]);

  useEffect(() => {
    void primeCsrf();
  }, []);

  const meQuery = useQuery<Me | null>({
    queryKey: ["me", isSignedIn],
    queryFn: async () => {
      try {
        return await api.me();
      } catch (error) {
        if (error instanceof ApiError && error.status === 401) return null;
        throw error;
      }
    },
    enabled: isLoaded,
    retry: false,
    staleTime: 60_000,
  });

  const logout = async () => {
    await signOut();
    queryClient.clear();
  };

  return (
    <AuthContext.Provider
      value={{
        user: meQuery.data ?? null,
        loading: !isLoaded || (!!isSignedIn && meQuery.isLoading),
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
  if (!user)
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
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
