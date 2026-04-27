import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { useAuthStore } from './store/authStore';
import Sidebar from './components/Sidebar';
import AuthGuard from './features/auth/AuthGuard';
import LoginPage from './features/auth/LoginPage';
import RegisterPage from './features/auth/RegisterPage';
import DashboardPage from './features/dashboard/DashboardPage';
import TaskListPage from './features/tasks/TaskListPage';
import TaskBoardView from './features/tasks/TaskBoardView';
import MembersPage from './features/organizations/MembersPage';
import InvitePage from './features/organizations/InvitePage';
import OrgSettingsPage from './features/organizations/OrgSettingsPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30_000,
      refetchOnWindowFocus: false,
    },
  },
});

function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="app-layout">
      <Sidebar />
      <main className="app-content">
        {children}
      </main>
    </div>
  );
}

function App() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              background: '#1e1e2e',
              color: '#e8e8ed',
              border: '1px solid #2a2a3d',
              borderRadius: '8px',
              fontSize: '14px',
            },
          }}
        />

        <Routes>
          {/* Public routes */}
          <Route
            path="/login"
            element={isAuthenticated ? <Navigate to="/" replace /> : <LoginPage />}
          />
          <Route
            path="/register"
            element={isAuthenticated ? <Navigate to="/" replace /> : <RegisterPage />}
          />

          {/* Protected routes */}
          <Route
            path="/"
            element={
              <AuthGuard>
                <AppLayout><DashboardPage /></AppLayout>
              </AuthGuard>
            }
          />
          <Route
            path="/tasks"
            element={
              <AuthGuard>
                <AppLayout><TaskListPage /></AppLayout>
              </AuthGuard>
            }
          />
          <Route
            path="/board"
            element={
              <AuthGuard>
                <AppLayout><TaskBoardView /></AppLayout>
              </AuthGuard>
            }
          />
          <Route
            path="/members"
            element={
              <AuthGuard>
                <AppLayout><MembersPage /></AppLayout>
              </AuthGuard>
            }
          />
          <Route
            path="/invites"
            element={
              <AuthGuard>
                <AppLayout><InvitePage /></AppLayout>
              </AuthGuard>
            }
          />
          <Route
            path="/settings"
            element={
              <AuthGuard>
                <AppLayout><OrgSettingsPage /></AppLayout>
              </AuthGuard>
            }
          />

          {/* Catch-all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
