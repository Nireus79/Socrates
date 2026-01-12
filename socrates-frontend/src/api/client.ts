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

// Initialize API_BASE_URL with fallback chain:
// 1. Try to load from API's port-config endpoint (dynamic port allocation)
// 2. Try to load from server-config.json (written by full-stack startup)
// 3. Fall back to environment variable
// 4. Final fallback to localhost:8000
let API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Store callback for when config is loaded
let onConfigLoaded: ((url: string) => void) | null = null;

// Attempt to detect API on a specific port
const tryPort = async (port: number): Promise<boolean> => {
  try {
    const url = `http://127.0.0.1:${port}/health`;
    const response = await fetch(url, { method: 'GET', signal: AbortSignal.timeout(2000) });
    return response.ok;
  } catch {
    return false;
  }
};

// Load server config if available
const loadServerConfig = async () => {
  // Strategy 1: Try to load from API's /port-config endpoint on common ports
  console.log('[APIClient] Attempting to discover API port from /port-config endpoint...');
  for (let port = 8008; port <= 8020; port++) {
    try {
      const response = await fetch(`http://127.0.0.1:${port}/port-config`, {
        method: 'GET',
        signal: AbortSignal.timeout(1000),
      });
      if (response.ok) {
        const config = await response.json();
        if (config.api && config.api.url) {
          API_BASE_URL = config.api.url;
          console.log('[APIClient] Discovered API from /port-config endpoint:', API_BASE_URL);
          if (onConfigLoaded) {
            onConfigLoaded(API_BASE_URL);
          }
          return;
        }
      }
    } catch {
      // Continue to next port
    }
  }
  console.log('[APIClient] Could not discover API from /port-config endpoint');

  // Strategy 2: Try to load from port-config.json in current directory
  try {
    console.log('[APIClient] Attempting to load port config from /port-config.json...');
    const response = await fetch('/port-config.json', {
      signal: AbortSignal.timeout(1000),
    });
    if (response.ok) {
      const config = await response.json();
      if (config.api && config.api.url) {
        API_BASE_URL = config.api.url;
        console.log('[APIClient] Loaded API URL from port-config.json:', API_BASE_URL);
        if (onConfigLoaded) {
          onConfigLoaded(API_BASE_URL);
        }
        return;
      }
    }
  } catch (error) {
    console.debug('[APIClient] Could not load port-config.json');
  }

  // Strategy 3: Try to load from server-config.json (legacy support)
  try {
    console.log('[APIClient] Attempting to load from server-config.json...');
    const response = await fetch('/server-config.json', {
      signal: AbortSignal.timeout(1000),
    });
    if (response.ok) {
      const config = await response.json();
      if (config.api_url) {
        API_BASE_URL = config.api_url;
        console.log('[APIClient] Loaded API URL from server config:', API_BASE_URL);
        if (onConfigLoaded) {
          onConfigLoaded(API_BASE_URL);
        }
        return;
      }
    }
  } catch (error) {
    console.debug('[APIClient] Could not load server-config.json');
  }

  // Strategy 4: Try common ports as health check fallback
  console.log('[APIClient] Attempting health check on common ports...');
  for (let port = 8008; port <= 8020; port++) {
    try {
      if (await tryPort(port)) {
        API_BASE_URL = `http://127.0.0.1:${port}`;
        console.log('[APIClient] Auto-detected API on port:', port);
        if (onConfigLoaded) {
          onConfigLoaded(API_BASE_URL);
        }
        return;
      }
    } catch {
      // Continue to next port
    }
  }

  console.log('[APIClient] Using configured/default API URL:', API_BASE_URL);
};

// Call on module load
loadServerConfig();

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
      timeout: config.timeout || 60000,  // 60 seconds to accommodate slow operations (Claude API, large data loads)
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Load tokens from localStorage
    this.loadTokens();

    // Setup request interceptor
    this.client.interceptors.request.use(
      async (config: InternalAxiosRequestConfig) => {
        // Proactively refresh token if needed
        await this.proactiveTokenRefresh();
        // Then inject the (possibly refreshed) token
        return this.injectToken(config);
      },
      (error) => Promise.reject(error)
    );

    // Setup response interceptor
    this.client.interceptors.response.use(
      (response) => {
        // Automatically unwrap APIResponse wrapper
        // If response.data has success/status fields (APIResponse format),
        // extract and return just the data field
        if (response.data && typeof response.data === 'object') {
          if ('success' in response.data && 'status' in response.data) {
            // This is an APIResponse wrapper - extract the data
            const wrappedData = response.data as any;
            if (wrappedData.data !== undefined) {
              response.data = wrappedData.data;
            }
          }
        }
        return response;
      },
      (error) => this.handleResponseError(error)
    );

    // Register callback to update baseURL when server config is loaded
    onConfigLoaded = (url: string) => {
      this.client.defaults.baseURL = url;
      console.log('[APIClient] Updated baseURL to:', url);
    };
  }

  /**
   * Load tokens from localStorage
   */
  private loadTokens(): void {
    this.accessToken = localStorage.getItem('access_token');
    this.refreshToken = localStorage.getItem('refresh_token');
    console.log('[APIClient] Tokens loaded on init:', {
      hasAccessToken: !!this.accessToken,
      hasRefreshToken: !!this.refreshToken,
      tokenLength: this.accessToken?.length,
    });
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
   * Check if access token is expired
   */
  private isTokenExpired(token: string): boolean {
    try {
      const parts = token.split('.');
      if (parts.length !== 3) return true;

      const payload = JSON.parse(atob(parts[1]));
      const expiresAt = payload.exp * 1000; // Convert to milliseconds
      const now = Date.now();
      const expired = now > expiresAt;

      if (expired) {
        console.warn('[APIClient] Access token is EXPIRED:', {
          expiresAt: new Date(expiresAt).toISOString(),
          now: new Date(now).toISOString(),
        });
      }
      return expired;
    } catch (error) {
      console.error('[APIClient] Error checking token expiration:', error);
      return true; // Assume expired if we can't parse
    }
  }

  /**
   * Inject JWT token into request headers
   * Also proactively refreshes if token is expired
   */
  private injectToken(config: InternalAxiosRequestConfig): InternalAxiosRequestConfig {
    if (this.accessToken) {
      // Check if token is expired before using it
      if (this.isTokenExpired(this.accessToken)) {
        console.warn('[APIClient] Expired token detected, will attempt refresh on 401');
      }

      config.headers.Authorization = `Bearer ${this.accessToken}`;
      console.log('[APIClient] Token injected for request:', config.url);
    } else {
      console.warn('[APIClient] NO TOKEN available for request:', config.url, {
        hasAccessToken: !!this.accessToken,
        localStorageToken: !!localStorage.getItem('access_token'),
      });
    }

    // Include testing mode header if enabled (for subscription testing)
    const testingMode = localStorage.getItem('socrates_testing_mode');
    const testingExpires = localStorage.getItem('socrates_testing_mode_expires');
    if (testingMode === 'enabled' && testingExpires) {
      const expiresAt = parseInt(testingExpires, 10);
      if (Date.now() < expiresAt) {
        config.headers['X-Testing-Mode'] = 'enabled';
        console.log('[APIClient] Testing mode header included');
      }
    }

    return config;
  }

  /**
   * Proactively refresh token if it's about to expire
   * This prevents 401 errors by refreshing before expiry
   */
  private async proactiveTokenRefresh(): Promise<void> {
    if (!this.accessToken || !this.refreshToken) {
      return; // No tokens to refresh
    }

    try {
      const parts = this.accessToken.split('.');
      if (parts.length !== 3) return;

      const payload = JSON.parse(atob(parts[1]));
      const expiresAt = payload.exp * 1000;
      const now = Date.now();
      const timeUntilExpiry = expiresAt - now;
      const REFRESH_THRESHOLD = 2 * 60 * 1000; // Refresh if less than 2 minutes left

      if (timeUntilExpiry < REFRESH_THRESHOLD && !this.isRefreshing) {
        console.log('[APIClient] Token expiring soon, proactively refreshing...');
        this.isRefreshing = true;

        try {
          const response = await this.refreshAccessToken();
          this.saveTokens(response.access_token, response.refresh_token);
          console.log('[APIClient] Token proactively refreshed successfully');
        } catch (error) {
          console.error('[APIClient] Proactive token refresh failed:', error);
          // Don't throw - let the request proceed, it will handle 401 normally
        } finally {
          this.isRefreshing = false;
        }
      }
    } catch (error) {
      // Silently ignore errors in proactive refresh check
      console.debug('[APIClient] Error in proactive refresh check:', error);
    }
  }

  /**
   * Handle response errors including token refresh
   */
  private async handleResponseError(error: AxiosError): Promise<any> {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // Log all errors for debugging
    console.error('[APIClient] Response error:', {
      status: error.response?.status,
      url: originalRequest.url,
      message: error.message,
      detail: (error.response?.data as any)?.detail,
    });

    // If error is 401 and we haven't already retried
    if (error.response?.status === 401 && !originalRequest._retry) {
      console.warn('[APIClient] Received 401 Unauthorized, attempting token refresh...');
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
    try {
      console.log('[APIClient] Attempting to refresh access token...');
      const response = await axios.post(
        `${API_BASE_URL}/auth/refresh`,
        { refresh_token: this.refreshToken },
        { timeout: 10000 }
      );
      console.log('[APIClient] Token refresh successful');
      return response.data;
    } catch (error) {
      console.error('[APIClient] Token refresh failed:', error instanceof Error ? error.message : error);
      throw error;
    }
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
    console.log('[APIClient] setTokens called with:', {
      hasAccessToken: !!accessToken,
      hasRefreshToken: !!refreshToken,
      accessTokenLength: accessToken?.length,
    });
    this.saveTokens(accessToken, refreshToken);
    console.log('[APIClient] Tokens saved. Current state:', {
      accessTokenSet: !!this.accessToken,
      refreshTokenSet: !!this.refreshToken,
    });
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
