/**
 * Authentication API service
 */

import { apiClient } from './client';
import type { AuthResponse, User, TokenResponse } from '../types/models';
import type { RegisterRequest, LoginRequest, RefreshTokenRequest } from '../types/api';

export const authAPI = {
  /**
   * Register a new user
   */
  async register(credentials: RegisterRequest): Promise<AuthResponse> {
    return apiClient.post<AuthResponse>('/auth/register', credentials);
  },

  /**
   * Login with credentials
   */
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    return apiClient.post<AuthResponse>('/auth/login', credentials);
  },

  /**
   * Refresh access token
   */
  async refreshToken(request: RefreshTokenRequest): Promise<TokenResponse> {
    return apiClient.post<TokenResponse>('/auth/refresh', request);
  },

  /**
   * Get current user profile
   */
  async getCurrentUser(): Promise<User> {
    return apiClient.get<User>('/auth/me');
  },

  /**
   * Logout
   */
  async logout(): Promise<void> {
    await apiClient.post('/auth/logout', {});
  },

  /**
   * Update user profile
   */
  async updateProfile(data: Partial<User>): Promise<User> {
    return apiClient.put<User>('/auth/me', data);
  },

  /**
   * Delete user account permanently
   */
  async deleteAccount(): Promise<void> {
    await apiClient.delete('/auth/me');
  },

  /**
   * Toggle testing mode (bypasses subscription checks)
   */
  async setTestingMode(enabled: boolean): Promise<void> {
    await apiClient.put(`/auth/me/testing-mode?enabled=${enabled}`, {});
  },
};
