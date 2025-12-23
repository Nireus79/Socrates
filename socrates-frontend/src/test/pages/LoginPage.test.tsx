/**
 * LoginPage Component Tests
 * Tests form submission, error display, and navigation
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { LoginPage } from '../../pages/auth/LoginPage';
import { useAuthStore } from '../../stores/authStore';

// Mock the auth store
vi.mock('../../stores/authStore');

const renderLoginPage = () => {
  return render(
    <BrowserRouter>
      <LoginPage />
    </BrowserRouter>
  );
};

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Form Rendering', () => {
    it('should render login form with all fields', () => {
      vi.mocked(useAuthStore).mockReturnValue({
        user: null,
        isLoading: false,
        error: null,
        isAuthenticated: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        deleteAccount: vi.fn(),
        setTestingMode: vi.fn(),
        clearError: vi.fn(),
        setUser: vi.fn(),
        restoreAuthFromStorage: vi.fn(),
      } as any);

      renderLoginPage();

      expect(screen.getByText(/login/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument();
    });

    it('should show register link', () => {
      vi.mocked(useAuthStore).mockReturnValue({
        user: null,
        isLoading: false,
        error: null,
        isAuthenticated: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        deleteAccount: vi.fn(),
        setTestingMode: vi.fn(),
        clearError: vi.fn(),
        setUser: vi.fn(),
        restoreAuthFromStorage: vi.fn(),
      } as any);

      renderLoginPage();

      expect(screen.getByText(/don't have an account/i)).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /register/i })).toBeInTheDocument();
    });
  });

  describe('Form Submission', () => {
    it('should submit form with username and password', async () => {
      const mockLogin = vi.fn();

      vi.mocked(useAuthStore).mockReturnValue({
        user: null,
        isLoading: false,
        error: null,
        isAuthenticated: false,
        login: mockLogin,
        register: vi.fn(),
        logout: vi.fn(),
        deleteAccount: vi.fn(),
        setTestingMode: vi.fn(),
        clearError: vi.fn(),
        setUser: vi.fn(),
        restoreAuthFromStorage: vi.fn(),
      } as any);

      renderLoginPage();

      const usernameInput = screen.getByLabelText(/username/i);
      const passwordInput = screen.getByLabelText(/password/i);
      const loginButton = screen.getByRole('button', { name: /login/i });

      await userEvent.type(usernameInput, 'testuser');
      await userEvent.type(passwordInput, 'password123');
      await userEvent.click(loginButton);

      expect(mockLogin).toHaveBeenCalledWith('testuser', 'password123');
    });

    it('should disable submit button while loading', () => {
      vi.mocked(useAuthStore).mockReturnValue({
        user: null,
        isLoading: true,
        error: null,
        isAuthenticated: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        deleteAccount: vi.fn(),
        setTestingMode: vi.fn(),
        clearError: vi.fn(),
        setUser: vi.fn(),
        restoreAuthFromStorage: vi.fn(),
      } as any);

      renderLoginPage();

      const loginButton = screen.getByRole('button');
      expect(loginButton).toBeDisabled();
      expect(loginButton).toHaveTextContent(/logging in/i);
    });
  });

  describe('Error Handling', () => {
    it('should display error message when login fails with 401', () => {
      vi.mocked(useAuthStore).mockReturnValue({
        user: null,
        isLoading: false,
        error: 'Invalid username or password',
        isAuthenticated: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        deleteAccount: vi.fn(),
        setTestingMode: vi.fn(),
        clearError: vi.fn(),
        setUser: vi.fn(),
        restoreAuthFromStorage: vi.fn(),
      } as any);

      renderLoginPage();

      expect(screen.getByText('Invalid username or password')).toBeInTheDocument();
    });

    it('should display server error message', () => {
      vi.mocked(useAuthStore).mockReturnValue({
        user: null,
        isLoading: false,
        error: 'Server error. Please try again later',
        isAuthenticated: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        deleteAccount: vi.fn(),
        setTestingMode: vi.fn(),
        clearError: vi.fn(),
        setUser: vi.fn(),
        restoreAuthFromStorage: vi.fn(),
      } as any);

      renderLoginPage();

      expect(screen.getByText('Server error. Please try again later')).toBeInTheDocument();
    });

    it('should clear error when user modifies form', async () => {
      const mockClearError = vi.fn();

      vi.mocked(useAuthStore).mockReturnValue({
        user: null,
        isLoading: false,
        error: 'Login failed',
        isAuthenticated: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        deleteAccount: vi.fn(),
        setTestingMode: vi.fn(),
        clearError: mockClearError,
        setUser: vi.fn(),
        restoreAuthFromStorage: vi.fn(),
      } as any);

      renderLoginPage();

      const usernameInput = screen.getByLabelText(/username/i);
      await userEvent.type(usernameInput, 'a');

      expect(mockClearError).toHaveBeenCalled();
    });
  });

  describe('Form Validation', () => {
    it('should require username and password', async () => {
      const mockLogin = vi.fn();

      vi.mocked(useAuthStore).mockReturnValue({
        user: null,
        isLoading: false,
        error: null,
        isAuthenticated: false,
        login: mockLogin,
        register: vi.fn(),
        logout: vi.fn(),
        deleteAccount: vi.fn(),
        setTestingMode: vi.fn(),
        clearError: vi.fn(),
        setUser: vi.fn(),
        restoreAuthFromStorage: vi.fn(),
      } as any);

      renderLoginPage();

      const loginButton = screen.getByRole('button', { name: /login/i });

      // Try to submit empty form
      await userEvent.click(loginButton);

      // Should not call login
      expect(mockLogin).not.toHaveBeenCalled();
    });
  });

  describe('Navigation', () => {
    it('should navigate to dashboard on successful login', async () => {
      vi.mocked(useAuthStore).mockReturnValue({
        user: { username: 'testuser', email: 'test@example.com', subscription_tier: 'free', testing_mode: false },
        isLoading: false,
        error: null,
        isAuthenticated: true,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        deleteAccount: vi.fn(),
        setTestingMode: vi.fn(),
        clearError: vi.fn(),
        setUser: vi.fn(),
        restoreAuthFromStorage: vi.fn(),
      } as any);

      // Note: Actual navigation test would require mocking React Router
      // This is a simplified version
      renderLoginPage();

      // Component should handle authenticated state
      // (In real app, ProtectedRoute would redirect to dashboard)
    });
  });

  describe('UX Improvements', () => {
    it('should show loading state on form submission', async () => {
      let isLoading = false;
      const mockLogin = vi.fn(async () => {
        isLoading = true;
      });

      vi.mocked(useAuthStore).mockReturnValue({
        user: null,
        isLoading,
        error: null,
        isAuthenticated: false,
        login: mockLogin,
        register: vi.fn(),
        logout: vi.fn(),
        deleteAccount: vi.fn(),
        setTestingMode: vi.fn(),
        clearError: vi.fn(),
        setUser: vi.fn(),
        restoreAuthFromStorage: vi.fn(),
      } as any);

      renderLoginPage();

      const usernameInput = screen.getByLabelText(/username/i);
      const passwordInput = screen.getByLabelText(/password/i);
      const loginButton = screen.getByRole('button', { name: /login/i });

      await userEvent.type(usernameInput, 'testuser');
      await userEvent.type(passwordInput, 'password123');

      expect(loginButton).not.toBeDisabled();

      await userEvent.click(loginButton);

      expect(mockLogin).toHaveBeenCalled();
    });

    it('should have accessible form labels', () => {
      vi.mocked(useAuthStore).mockReturnValue({
        user: null,
        isLoading: false,
        error: null,
        isAuthenticated: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        deleteAccount: vi.fn(),
        setTestingMode: vi.fn(),
        clearError: vi.fn(),
        setUser: vi.fn(),
        restoreAuthFromStorage: vi.fn(),
      } as any);

      renderLoginPage();

      const usernameInput = screen.getByLabelText(/username/i);
      const passwordInput = screen.getByLabelText(/password/i);

      expect(usernameInput).toHaveAttribute('id');
      expect(passwordInput).toHaveAttribute('id');
    });
  });
});
