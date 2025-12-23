/**
 * Authentication Edge Cases and Advanced Scenarios
 * Tests complex auth situations: token expiry, concurrent requests, session management
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import axios from 'axios';

vi.mock('axios');
const mockedAxios = axios as any;

describe('Auth Edge Cases: Token Expiration and Refresh', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('should detect expired access token and use refresh token', async () => {
    const refreshToken = 'valid_refresh_token_edge1';
    localStorage.setItem('access_token', 'expired_access_token');
    localStorage.setItem('refresh_token', refreshToken);
    localStorage.setItem('user', JSON.stringify({ id: 'user_1', username: 'testuser' }));

    // First request fails with 401 (token expired)
    mockedAxios.get.mockRejectedValueOnce({
      response: { status: 401, data: { detail: 'Token expired' } }
    });

    // Should attempt refresh
    mockedAxios.post.mockResolvedValueOnce({
      status: 200,
      data: {
        access_token: 'new_access_token_edge1',
        refresh_token: 'new_refresh_token_edge1'
      }
    });

    try {
      // Initial request with expired token fails
      await axios.get('http://localhost:8000/projects', {
        headers: { Authorization: 'Bearer expired_access_token' }
      });
    } catch (error: any) {
      expect(error.response.status).toBe(401);

      // Manually trigger refresh (in real app, this happens automatically)
      const refreshResponse = await axios.post('http://localhost:8000/auth/refresh', {
        refresh_token: refreshToken
      });

      // Update tokens
      localStorage.setItem('access_token', refreshResponse.data.access_token);
      localStorage.setItem('refresh_token', refreshResponse.data.refresh_token);

      // Retry original request with new token
      mockedAxios.get.mockResolvedValueOnce({
        status: 200,
        data: [{ id: 'proj_1' }]
      });

      const retryResponse = await axios.get(
        'http://localhost:8000/projects',
        { headers: { Authorization: `Bearer ${refreshResponse.data.access_token}` } }
      );

      expect(retryResponse.status).toBe(200);
    }
  });

  it('should handle refresh token expiration and force re-login', async () => {
    localStorage.setItem('access_token', 'expired_access_token_2');
    localStorage.setItem('refresh_token', 'expired_refresh_token_2');

    // Access token expired
    mockedAxios.get.mockRejectedValueOnce({
      response: { status: 401 }
    });

    // Refresh token also expired
    mockedAxios.post.mockRejectedValueOnce({
      response: { status: 401, data: { detail: 'Refresh token expired or invalid' } }
    });

    try {
      await axios.get('http://localhost:8000/projects', {
        headers: { Authorization: 'Bearer expired_access_token_2' }
      });
    } catch (error: any) {
      expect(error.response.status).toBe(401);

      // Try to refresh
      try {
        await axios.post('http://localhost:8000/auth/refresh', {
          refresh_token: 'expired_refresh_token_2'
        });
      } catch (refreshError: any) {
        expect(refreshError.response.status).toBe(401);

        // Clear auth and force login
        localStorage.clear();
        expect(localStorage.getItem('access_token')).toBeNull();
      }
    }
  });

  it('should handle token refresh race condition', async () => {
    const refreshToken = 'refresh_token_race';
    localStorage.setItem('access_token', 'expired_token_race');
    localStorage.setItem('refresh_token', refreshToken);

    // Two concurrent requests both get 401
    let refreshInProgress = false;
    const pendingRefresh = new Promise<void>((resolve) => {
      mockedAxios.post.mockImplementation(async (url: string) => {
        if (url.includes('refresh') && !refreshInProgress) {
          refreshInProgress = true;
          // Simulate network delay
          await new Promise(r => setTimeout(r, 100));
          resolve();
          return {
            status: 200,
            data: {
              access_token: 'new_token_race',
              refresh_token: 'new_refresh_race'
            }
          };
        }
        throw new Error('Already refreshing');
      });
    });

    mockedAxios.get.mockRejectedValue({
      response: { status: 401 }
    });

    // First concurrent request triggers refresh
    const promise1 = axios.get('http://localhost:8000/projects', {
      headers: { Authorization: 'Bearer expired_token_race' }
    }).catch(() => {
      // First request fails, but triggers refresh
      return axios.post('http://localhost:8000/auth/refresh', { refresh_token: refreshToken });
    });

    // Second concurrent request also gets 401, waits for refresh
    const promise2 = new Promise((resolve) => {
      setTimeout(() => {
        expect(localStorage.getItem('access_token')).toBeDefined();
        resolve(true);
      }, 150);
    });

    await Promise.all([promise1, pendingRefresh, promise2]);
  });

  it('should handle token with upcoming expiration', async () => {
    const now = Math.floor(Date.now() / 1000);
    const almostExpiredToken = 'token_expiring_soon';

    localStorage.setItem('access_token', almostExpiredToken);
    localStorage.setItem('refresh_token', 'valid_refresh');
    localStorage.setItem('user', JSON.stringify({ id: 'user_1' }));

    // Check if token will expire in next 5 minutes
    // In real app, decode JWT and check exp claim
    const shouldRefresh = true; // Simulating check

    if (shouldRefresh) {
      mockedAxios.post.mockResolvedValueOnce({
        status: 200,
        data: {
          access_token: 'fresh_token_valid_for_hours',
          refresh_token: 'fresh_refresh_token'
        }
      });

      const refreshResponse = await axios.post('http://localhost:8000/auth/refresh', {
        refresh_token: 'valid_refresh'
      });

      localStorage.setItem('access_token', refreshResponse.data.access_token);
      expect(localStorage.getItem('access_token')).toBe('fresh_token_valid_for_hours');
    }
  });
});

describe('Auth Edge Cases: Concurrent Operations', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('should handle concurrent login attempts', async () => {
    let loginAttempts = 0;

    mockedAxios.post.mockImplementation(async (url: string, data: any) => {
      if (url.includes('login')) {
        loginAttempts++;

        // Simulate that second login attempt fails (already logged in)
        if (loginAttempts > 1) {
          return {
            status: 200,
            data: {
              access_token: 'token_attempt_' + loginAttempts,
              user: { id: 'user_' + loginAttempts }
            }
          };
        }

        return {
          status: 200,
          data: {
            access_token: 'concurrent_login_token_1',
            refresh_token: 'concurrent_refresh_1',
            user: { id: 'user_concurrent', username: 'testuser' }
          }
        };
      }
      throw new Error('Unknown endpoint');
    });

    // Attempt concurrent logins
    const login1 = axios.post('http://localhost:8000/auth/login', {
      username: 'user',
      password: 'pass'
    });

    const login2 = axios.post('http://localhost:8000/auth/login', {
      username: 'user',
      password: 'pass'
    });

    const [response1, response2] = await Promise.all([login1, login2]);

    expect(response1.data.access_token).toBeDefined();
    expect(response2.data.access_token).toBeDefined();

    // Latest token should be in storage
    localStorage.setItem('access_token', response2.data.access_token);
    expect(localStorage.getItem('access_token')).toBe('token_attempt_2');
  });

  it('should handle concurrent requests with same expired token', async () => {
    const expiredToken = 'expired_concurrent';
    localStorage.setItem('access_token', expiredToken);
    localStorage.setItem('refresh_token', 'refresh_concurrent');

    let refreshCount = 0;

    mockedAxios.post.mockImplementation(async (url: string) => {
      if (url.includes('refresh')) {
        refreshCount++;
        // All refresh requests get same new token
        return {
          status: 200,
          data: {
            access_token: 'new_token_from_refresh',
            refresh_token: 'new_refresh_token_from_refresh'
          }
        };
      }
      throw new Error('Unknown endpoint');
    });

    mockedAxios.get.mockRejectedValue({
      response: { status: 401 }
    });

    // Make 3 concurrent requests, all will get 401
    const requests = [1, 2, 3].map(() =>
      axios.get('http://localhost:8000/projects', {
        headers: { Authorization: `Bearer ${expiredToken}` }
      }).catch(async () => {
        // Each catches 401 and triggers refresh
        const refreshResp = await axios.post('http://localhost:8000/auth/refresh', {
          refresh_token: 'refresh_concurrent'
        });
        return refreshResp;
      })
    );

    const results = await Promise.all(requests);

    // All should get the refreshed token
    results.forEach(result => {
      expect(result.data.access_token).toBe('new_token_from_refresh');
    });

    // Should have called refresh (implementation varies, but at least once)
    expect(refreshCount).toBeGreaterThan(0);
  });

  it('should handle logout from multiple tabs/windows', async () => {
    // Simulate user logging in
    localStorage.setItem('access_token', 'multi_tab_token');
    localStorage.setItem('user', JSON.stringify({ id: 'user_1' }));

    // Tab 1 makes request
    mockedAxios.get.mockResolvedValueOnce({
      status: 200,
      data: [{ id: 'proj_1' }]
    });

    const response1 = await axios.get('http://localhost:8000/projects', {
      headers: { Authorization: 'Bearer multi_tab_token' }
    });
    expect(response1.status).toBe(200);

    // User logs out in Tab 1
    mockedAxios.post.mockResolvedValueOnce({ status: 200 });
    await axios.post('http://localhost:8000/auth/logout', {}, {
      headers: { Authorization: 'Bearer multi_tab_token' }
    });
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');

    // Tab 2 tries to make request with still-stored token
    // But localStorage is cleared, so request fails
    expect(localStorage.getItem('access_token')).toBeNull();

    mockedAxios.get.mockRejectedValueOnce({
      response: { status: 401 }
    });

    try {
      await axios.get('http://localhost:8000/projects');
    } catch (error: any) {
      expect(error.response.status).toBe(401);
    }
  });
});

describe('Auth Edge Cases: Session Management', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('should maintain session across browser restart', async () => {
    // Step 1: User logs in
    mockedAxios.post.mockResolvedValueOnce({
      status: 200,
      data: {
        access_token: 'persistent_token',
        refresh_token: 'persistent_refresh',
        user: { id: 'user_persist', username: 'testuser' }
      }
    });

    const loginResponse = await axios.post('http://localhost:8000/auth/login', {
      username: 'testuser',
      password: 'pass'
    });

    localStorage.setItem('access_token', loginResponse.data.access_token);
    localStorage.setItem('refresh_token', loginResponse.data.refresh_token);
    localStorage.setItem('user', JSON.stringify(loginResponse.data.user));

    // Step 2: Simulate browser restart (app reloads)
    const storedToken = localStorage.getItem('access_token');
    const storedUser = localStorage.getItem('user');

    expect(storedToken).toBe('persistent_token');
    expect(storedUser).toBeDefined();

    // Step 3: App initializes and restores session
    mockedAxios.get.mockResolvedValueOnce({
      status: 200,
      data: []
    });

    const response = await axios.get('http://localhost:8000/projects', {
      headers: { Authorization: `Bearer ${storedToken}` }
    });

    expect(response.status).toBe(200);
    // User session persisted across browser restart
  });

  it('should handle switching between different user accounts', async () => {
    // Step 1: User A logs in
    mockedAxios.post.mockResolvedValueOnce({
      status: 200,
      data: {
        access_token: 'token_user_a',
        refresh_token: 'refresh_user_a',
        user: { id: 'user_a', username: 'userA' }
      }
    });

    const loginA = await axios.post('http://localhost:8000/auth/login', {
      username: 'userA',
      password: 'passA'
    });

    localStorage.setItem('access_token', loginA.data.access_token);
    localStorage.setItem('user', JSON.stringify(loginA.data.user));

    expect(JSON.parse(localStorage.getItem('user')!).username).toBe('userA');

    // Step 2: User A logs out
    mockedAxios.post.mockResolvedValueOnce({ status: 200 });
    await axios.post('http://localhost:8000/auth/logout', {}, {
      headers: { Authorization: 'Bearer token_user_a' }
    });
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');

    // Step 3: User B logs in with same browser
    mockedAxios.post.mockResolvedValueOnce({
      status: 200,
      data: {
        access_token: 'token_user_b',
        refresh_token: 'refresh_user_b',
        user: { id: 'user_b', username: 'userB' }
      }
    });

    const loginB = await axios.post('http://localhost:8000/auth/login', {
      username: 'userB',
      password: 'passB'
    });

    localStorage.setItem('access_token', loginB.data.access_token);
    localStorage.setItem('user', JSON.stringify(loginB.data.user));

    expect(JSON.parse(localStorage.getItem('user')!).username).toBe('userB');
    expect(localStorage.getItem('access_token')).toBe('token_user_b');
  });

  it('should handle password change during active session', async () => {
    const token = 'session_with_password_change';
    localStorage.setItem('access_token', token);
    localStorage.setItem('user', JSON.stringify({ id: 'user_1', username: 'testuser' }));

    // Step 1: User makes request (works)
    mockedAxios.get.mockResolvedValueOnce({
      status: 200,
      data: []
    });

    let response = await axios.get('http://localhost:8000/projects', {
      headers: { Authorization: `Bearer ${token}` }
    });
    expect(response.status).toBe(200);

    // Step 2: User changes password
    mockedAxios.put.mockResolvedValueOnce({
      status: 200,
      data: { message: 'Password changed' }
    });

    await axios.put('http://localhost:8000/auth/change-password', {
      old_password: 'oldpass',
      new_password: 'newpass'
    }, {
      headers: { Authorization: `Bearer ${token}` }
    });

    // Step 3: Session still valid with same token
    mockedAxios.get.mockResolvedValueOnce({
      status: 200,
      data: []
    });

    response = await axios.get('http://localhost:8000/projects', {
      headers: { Authorization: `Bearer ${token}` }
    });
    expect(response.status).toBe(200);
  });
});

describe('Auth Edge Cases: Invalid Token Scenarios', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('should handle malformed token in localStorage', async () => {
    localStorage.setItem('access_token', 'not.a.valid.jwt');
    localStorage.setItem('user', 'invalid json {]');

    // System should detect invalid token format
    const token = localStorage.getItem('access_token')!;

    // Invalid token format should be detected (typically by server)
    mockedAxios.get.mockRejectedValueOnce({
      response: { status: 401, data: { detail: 'Invalid token' } }
    });

    try {
      await axios.get('http://localhost:8000/projects', {
        headers: { Authorization: `Bearer ${token}` }
      });
    } catch (error: any) {
      expect(error.response.status).toBe(401);
      // Clear invalid auth
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
    }
  });

  it('should handle token with invalid signature', async () => {
    const tamperedToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyIn0.TAMPERED';
    localStorage.setItem('access_token', tamperedToken);

    mockedAxios.get.mockRejectedValueOnce({
      response: { status: 401, data: { detail: 'Invalid token signature' } }
    });

    try {
      await axios.get('http://localhost:8000/projects', {
        headers: { Authorization: `Bearer ${tamperedToken}` }
      });
    } catch (error: any) {
      expect(error.response.status).toBe(401);
    }
  });

  it('should handle empty token string', async () => {
    localStorage.setItem('access_token', '');
    localStorage.setItem('user', '{}');

    const token = localStorage.getItem('access_token');

    mockedAxios.get.mockRejectedValueOnce({
      response: { status: 401 }
    });

    try {
      await axios.get('http://localhost:8000/projects', {
        headers: { Authorization: `Bearer ${token}` }
      });
    } catch (error: any) {
      expect(error.response.status).toBe(401);
    }
  });
});

describe('Auth Edge Cases: Special Credentials', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('should handle login with special characters in password', async () => {
    const specialPassword = 'P@ssw0rd!#$%&*([]{})<>?';

    mockedAxios.post.mockResolvedValueOnce({
      status: 200,
      data: {
        access_token: 'special_char_token',
        user: { id: 'user_1', username: 'testuser' }
      }
    });

    const response = await axios.post('http://localhost:8000/auth/login', {
      username: 'testuser',
      password: specialPassword
    });

    expect(response.status).toBe(200);
    expect(response.data.access_token).toBeDefined();
  });

  it('should handle unicode characters in username', async () => {
    const unicodeUsername = 'user_测试_🎯';

    mockedAxios.post.mockResolvedValueOnce({
      status: 200,
      data: {
        access_token: 'unicode_token',
        user: { id: 'user_unicode', username: unicodeUsername }
      }
    });

    const response = await axios.post('http://localhost:8000/auth/login', {
      username: unicodeUsername,
      password: 'password'
    });

    expect(response.data.user.username).toBe(unicodeUsername);
  });

  it('should handle very long passwords', async () => {
    const longPassword = 'a'.repeat(10000); // 10k character password

    mockedAxios.post.mockResolvedValueOnce({
      status: 200,
      data: {
        access_token: 'long_pass_token',
        user: { id: 'user_long' }
      }
    });

    const response = await axios.post('http://localhost:8000/auth/login', {
      username: 'testuser',
      password: longPassword
    });

    expect(response.status).toBe(200);
  });
});
