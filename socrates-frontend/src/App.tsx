/**
 * Main App Component - Route configuration and layout
 */

import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './stores';
import { apiClient } from './api/client';
import { LoginPage } from './pages/auth/LoginPage';
import { RegisterPage } from './pages/auth/RegisterPage';
import { DashboardPage } from './pages/dashboard/DashboardPage';
import { ProjectsPage } from './pages/projects/ProjectsPage';
import { ProjectDetailPage } from './pages/projects/ProjectDetailPage';
import { ChatPage } from './pages/chat/ChatPage';
import { CodePage } from './pages/code/CodePage';
import { AnalyticsPage } from './pages/analytics/AnalyticsPage';
import { CollaborationPage } from './pages/collaboration/CollaborationPage';
import { SettingsPage } from './pages/settings/SettingsPage';
import { KnowledgeBasePage } from './pages/knowledge/KnowledgeBasePage';
import { MainLayout } from './components/layout';
import { ErrorBoundary } from './components/common';
import { NotificationProvider } from './components/providers/NotificationProvider';
import './App.css';

/**
 * Protected Route Component
 */
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuthStore();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/auth/login" replace />;
  }

  return <>{children}</>;
}

/**
 * Public Route Component
 */
function PublicRoute({ children }: { children: React.ReactNode }) {
  const { user } = useAuthStore();

  if (user) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
}

function App() {
  // Initialize backend API on app mount
  React.useEffect(() => {
    const initializeBackend = async () => {
      try {
        // Backend will use ANTHROPIC_API_KEY env variable by default
        await apiClient.post('/initialize', {});
        console.log('Backend API initialized successfully');
      } catch (error) {
        console.error('Failed to initialize backend:', error);
        // Don't block app if initialization fails - user can still login
      }
    };

    initializeBackend();
  }, []);

  return (
    <ErrorBoundary>
      <NotificationProvider />
      <BrowserRouter>
        <Routes>
          {/* Auth Routes */}
          <Route
            path="/auth/login"
            element={
              <PublicRoute>
                <LoginPage />
              </PublicRoute>
            }
          />
          <Route
            path="/auth/register"
            element={
              <PublicRoute>
                <RegisterPage />
              </PublicRoute>
            }
          />

          {/* Protected Routes */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/projects"
            element={
              <ProtectedRoute>
                <ProjectsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/projects/:projectId"
            element={
              <ProtectedRoute>
                <ProjectDetailPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/chat"
            element={
              <ProtectedRoute>
                <ChatPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/chat/:projectId"
            element={
              <ProtectedRoute>
                <ChatPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/code"
            element={
              <ProtectedRoute>
                <CodePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/analytics"
            element={
              <ProtectedRoute>
                <AnalyticsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/projects/:projectId/analytics"
            element={
              <ProtectedRoute>
                <AnalyticsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/collaboration"
            element={
              <ProtectedRoute>
                <CollaborationPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings"
            element={
              <ProtectedRoute>
                <SettingsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/knowledge"
            element={
              <ProtectedRoute>
                <KnowledgeBasePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/projects/:projectId/knowledge"
            element={
              <ProtectedRoute>
                <KnowledgeBasePage />
              </ProtectedRoute>
            }
          />

          {/* Documentation Route */}
          <Route
            path="/docs"
            element={
              <ProtectedRoute>
                <div className="min-h-screen bg-white dark:bg-gray-900 p-8">
                  <div className="max-w-4xl mx-auto">
                    <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-8">Documentation</h1>
                    <div className="prose dark:prose-invert max-w-none">
                      <p className="text-gray-600 dark:text-gray-400 mb-6">
                        Welcome to Socrates documentation. For API documentation, visit:
                      </p>
                      <ul className="list-disc pl-6 space-y-2 text-gray-600 dark:text-gray-400">
                        <li><a href="/docs" className="text-blue-600 hover:underline">Swagger UI - /docs</a></li>
                        <li><a href="/redoc" className="text-blue-600 hover:underline">ReDoc - /redoc</a></li>
                      </ul>
                    </div>
                  </div>
                </div>
              </ProtectedRoute>
            }
          />

          {/* Root redirect */}
          <Route path="/" element={<Navigate to="/auth/login" replace />} />

          {/* 404 */}
          <Route
            path="*"
            element={
              <div className="flex items-center justify-center min-h-screen">
                <div className="text-center">
                  <h1 className="text-6xl font-bold text-gray-900 dark:text-white mb-4">404</h1>
                  <p className="text-xl text-gray-600 dark:text-gray-400 mb-8">Page not found</p>
                  <a href="/auth/login" className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                    Go to Login
                  </a>
                </div>
              </div>
            }
          />
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  );
}

export default App;
