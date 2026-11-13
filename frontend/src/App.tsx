import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from './stores/authStore';
import { ThemeProvider, useTheme } from './stores/themeStore';
import Spinner from './components/ui/Spinner';

// Layouts
import DashboardLayout from './layouts/DashboardLayout';
import AuthLayout from './layouts/AuthLayout';

// Pages
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/auth/LoginPage';
import RegisterPage from './pages/auth/RegisterPage';

// Dashboard Sub-pages
import DashboardOverviewPage from './pages/dashboard/DashboardOverviewPage';
import PeoplePage from './pages/dashboard/PeoplePage';
import FaceRegistrationPage from './pages/dashboard/FaceRegistrationPage';
import LiveRecognitionPage from './pages/dashboard/LiveRecognitionPage';
import CamerasPage from './pages/dashboard/CamerasPage';
import AttendancePage from './pages/dashboard/AttendancePage';
import AnalyticsPage from './pages/dashboard/AnalyticsPage';
import ReportsPage from './pages/dashboard/ReportsPage';
import DepartmentsPage from './pages/dashboard/DepartmentsPage';
import ShiftsPage from './pages/dashboard/ShiftsPage';
import CorrectionsPage from './pages/dashboard/CorrectionsPage';
import NotificationsPage from './pages/dashboard/NotificationsPage';
import SettingsPage from './pages/dashboard/SettingsPage';
import AdminOrganizationsPage from './pages/dashboard/admin/AdminOrganizationsPage';
import AdminUsersPage from './pages/dashboard/admin/AdminUsersPage';
import AdminPlansPage from './pages/dashboard/admin/AdminPlansPage';
import AdminAuditLogsPage from './pages/dashboard/admin/AdminAuditLogsPage';

// Protected Route Guard
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-slate-50 dark:bg-slate-950">
        <div className="flex flex-col items-center gap-3">
          <Spinner size="lg" variant="primary" />
          <p className="text-xs font-semibold text-slate-500">Loading Attendora...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
};

// Public Route Guard (Redirects away from Login/Register if already authenticated)
const PublicAuthRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-slate-50 dark:bg-slate-950">
        <Spinner size="lg" variant="primary" />
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};

const ThemedToaster: React.FC = () => {
  const { isDark } = useTheme();

  return (
    <Toaster
      position="top-right"
      toastOptions={{
        duration: 3500,
        style: {
          background: isDark ? '#0f172a' : '#ffffff',
          color: isDark ? '#f8fafc' : '#0f172a',
          border: isDark ? '1px solid #1e293b' : '1px solid #e2e8f0',
          borderRadius: '0.75rem',
          fontSize: '0.8125rem',
          boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.05)',
        },
      }}
    />
  );
};

export const App: React.FC = () => {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <ThemedToaster />
          <Routes>
            {/* Public Landing Page */}
            <Route path="/" element={<LandingPage />} />

            {/* Public Auth Flow */}
            <Route
              element={
                <PublicAuthRoute>
                  <AuthLayout />
                </PublicAuthRoute>
              }
            >
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
            </Route>

            {/* Protected SaaS Workspace Dashboard */}
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <DashboardLayout />
                </ProtectedRoute>
              }
            >
              <Route index element={<DashboardOverviewPage />} />
              <Route path="people" element={<PeoplePage />} />
              <Route path="face-registration" element={<FaceRegistrationPage />} />
              <Route path="live-recognition" element={<LiveRecognitionPage />} />
              <Route path="cameras" element={<CamerasPage />} />
              <Route path="attendance" element={<AttendancePage />} />
              <Route path="analytics" element={<AnalyticsPage />} />
              <Route path="reports" element={<ReportsPage />} />
              <Route path="departments" element={<DepartmentsPage />} />
              <Route path="shifts" element={<ShiftsPage />} />
              <Route path="corrections" element={<CorrectionsPage />} />
              <Route path="notifications" element={<NotificationsPage />} />
              <Route path="settings" element={<SettingsPage />} />

              {/* Super Admin Routes */}
              <Route path="admin/organizations" element={<AdminOrganizationsPage />} />
              <Route path="admin/users" element={<AdminUsersPage />} />
              <Route path="admin/plans" element={<AdminPlansPage />} />
              <Route path="admin/audit-logs" element={<AdminAuditLogsPage />} />
            </Route>

            {/* Catch-all Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
};

export default App;
