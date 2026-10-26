import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/app/AppShell";
import { AdminRoute, ProtectedRoute } from "./lib/auth";
import { Spinner } from "./components/ui/Spinner";

const Landing = lazy(() => import("./pages/Landing"));
const AtsChecker = lazy(() => import("./pages/AtsChecker"));
const Legal = lazy(() => import("./pages/Legal"));
const NotFound = lazy(() => import("./pages/NotFound"));
const Login = lazy(() => import("./pages/auth/Login"));
const Signup = lazy(() => import("./pages/auth/Signup"));
const ForgotPassword = lazy(() => import("./pages/auth/ForgotPassword"));
const ResetPassword = lazy(() => import("./pages/auth/ResetPassword"));
const VerifyEmail = lazy(() => import("./pages/auth/VerifyEmail"));
const AuthCallback = lazy(() => import("./pages/auth/AuthCallback"));
const Dashboard = lazy(() => import("./pages/app/Dashboard"));
const Resumes = lazy(() => import("./pages/app/Resumes"));
const Jobs = lazy(() => import("./pages/app/Jobs"));
const Usage = lazy(() => import("./pages/app/Usage"));
const Billing = lazy(() => import("./pages/app/Billing"));
const Settings = lazy(() => import("./pages/app/Settings"));
const AppAts = lazy(() => import("./pages/app/AppAts"));
const Analytics = lazy(() => import("./pages/app/Analytics"));
const Profile = lazy(() => import("./pages/app/Profile"));
const ImportResume = lazy(() => import("./pages/app/ImportResume"));
const AdminPage = lazy(() => import("./pages/app/admin/AdminPage"));
const EditorPage = lazy(() => import("./pages/app/editor/EditorPage"));
const PublicProfilePage = lazy(() => import("./pages/public/PublicProfilePage"));
const PublicResumePage = lazy(() => import("./pages/public/PublicResumePage"));

export default function App() {
  return (
    <Suspense
      fallback={
        <div className="grid min-h-screen place-items-center bg-paper">
          <Spinner label="Loading Rezumiq" />
        </div>
      }
    >
      <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/ats-checker" element={<AtsChecker />} />
      <Route path="/legal/:page" element={<Legal />} />
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/account/verify-email/:key" element={<VerifyEmail />} />
      <Route path="/account/password/key/:key" element={<ResetPassword />} />
      <Route path="/auth/callback" element={<AuthCallback />} />

      <Route
        path="/app"
        element={
          <ProtectedRoute>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="resumes" element={<Resumes />} />
        <Route path="resumes/:id/edit" element={<EditorPage />} />
        <Route path="import" element={<ImportResume />} />
        <Route path="jobs" element={<Jobs />} />
        <Route path="ats" element={<AppAts />} />
        <Route path="analytics" element={<Analytics />} />
        <Route path="profile" element={<Profile />} />
        <Route
          path="admin"
          element={
            <AdminRoute>
              <AdminPage />
            </AdminRoute>
          }
        />
        <Route path="usage" element={<Usage />} />
        <Route path="billing" element={<Billing />} />
        <Route path="settings" element={<Settings />} />
        <Route path="*" element={<Navigate to="/app" replace />} />
      </Route>

      <Route path="/:username" element={<PublicProfilePage />} />
      <Route path="/:username/:slug" element={<PublicResumePage />} />

      <Route path="*" element={<NotFound />} />
      </Routes>
    </Suspense>
  );
}
