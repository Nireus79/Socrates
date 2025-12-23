/**
 * API Client - Axios instance with JWT interceptors
 *
 * Handles:
 * - Automatic JWT token injection
 * - Token refresh on expiry
 * - Error handling
 * - Request/response interceptors
 */

import axios from 'axios';
import type { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface APIClientConfig {
  baseURL?: string;
  timeout?: number;
}

class APIClient {
  private client: AxiosInstance;
  private accessToken: string | null = null;
  private refreshToken: string | null = null;
  private isRefreshing = false;
  private failedQueue: Array<{
    resolve: (token: string) => void;
    reject: (error: any) => void;
  }> = [];

  constructor(config: APIClientConfig = {}) {
    this.client = axios.create({
      baseURL: config.baseURL || API_BASE_URL,
      timeout: config.timeout || 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Load tokens from localStorage
    this.loadTokens();

    // Setup request interceptor
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => this.injectToken(config),
      (error) => Promise.reject(error)
    );

    // Setup response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error) => this.handleResponseError(error)
    );
  }

  /**
   * Load tokens from localStorage
   */
  private loadTokens(): void {
    this.accessToken = localStorage.getItem('access_token');
    this.refreshToken = localStorage.getItem('refresh_token');
  }

  /**
   * Save tokens to localStorage
   */
  private saveTokens(accessToken: string, refreshToken: string): void {
    this.accessToken = accessToken;
    this.refreshToken = refreshToken;
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
  }

  /**
   * Clear tokens from storage
   */
  private clearTokens(): void {
    this.accessToken = null;
    this.refreshToken = null;
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }

  /**
   * Inject JWT token into request headers
   */
  private injectToken(config: InternalAxiosRequestConfig): InternalAxiosRequestConfig {
    if (this.accessToken) {
      config.headers.Authorization = `Bearer ${this.accessToken}`;
    }
    return config;
  }

  /**
   * Handle response errors including token refresh
   */
  private async handleResponseError(error: AxiosError): Promise<any> {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // If error is 401 and we haven't already retried
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (this.isRefreshing) {
        // Queue request while token is being refreshed
        return new Promise((resolve, reject) => {
          this.failedQueue.push({
            resolve: (token: string) => {
              originalRequest.headers.Authorization = `Bearer ${token}`;
              resolve(this.client(originalRequest));
            },
            reject: (error) => reject(error),
          });
        });
      }

      originalRequest._retry = true;
      this.isRefreshing = true;

      try {
        // Attempt to refresh token
        if (this.refreshToken) {
          const response = await this.refreshAccessToken();
          this.saveTokens(response.access_token, response.refresh_token);

          // Process queued requests
          this.failedQueue.forEach((item) => item.resolve(response.access_token));
          this.failedQueue = [];

          // Retry original request
          originalRequest.headers.Authorization = `Bearer ${response.access_token}`;
          return this.client(originalRequest);
        } else {
          // No refresh token available
          this.clearTokens();
          window.location.href = '/auth/login';
          throw new Error('Session expired. Please login again.');
        }
      } catch (refreshError) {
        // Refresh failed
        this.clearTokens();
        this.failedQueue.forEach((item) => item.reject(refreshError));
        this.failedQueue = [];
        window.location.href = '/auth/login';
        throw refreshError;
      } finally {
        this.isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }

  /**
   * Refresh access token using refresh token
   */
  private async refreshAccessToken(): Promise<{ access_token: string; refresh_token: string }> {
    const response = await axios.post(
      `${API_BASE_URL}/auth/refresh`,
      { refresh_token: this.refreshToken },
      { timeout: 10000 }
    );
    return response.data;
  }

  /**
   * Get axios instance for advanced usage
   */
  getClient(): AxiosInstance {
    return this.client;
  }

  /**
   * Set authentication tokens
   */
  setTokens(accessToken: string, refreshToken: string): void {
    this.saveTokens(accessToken, refreshToken);
  }

  /**
   * Get current access token
   */
  getAccessToken(): string | null {
    return this.accessToken;
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return !!this.accessToken;
  }

  /**
   * Logout - clear tokens and redirect
   */
  logout(): void {
    this.clearTokens();
    window.location.href = '/auth/login';
  }

  // ============================================================================
  // Generic Request Methods
  // ============================================================================

  async get<T>(url: string, config?: any): Promise<T> {
    const response = await this.client.get<T>(url, config);
    return response.data;
  }

  async post<T>(url: string, data?: any, config?: any): Promise<T> {
    const response = await this.client.post<T>(url, data, config);
    return response.data;
  }

  async put<T>(url: string, data?: any, config?: any): Promise<T> {
    const response = await this.client.put<T>(url, data, config);
    return response.data;
  }

  async delete<T>(url: string, config?: any): Promise<T> {
    const response = await this.client.delete<T>(url, config);
    return response.data;
  }

  async patch<T>(url: string, data?: any, config?: any): Promise<T> {
    const response = await this.client.patch<T>(url, data, config);
    return response.data;
  }
}

// Create singleton instance
export const apiClient = new APIClient();
