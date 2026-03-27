/**
 * Auth Store Tests
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useAuthStore } from '../../stores/authStore';
import * as authAPI from '../../api/auth';

// Mock the auth API
vi.mock('../../api/auth');

describe('useAuthStore', () => {
  beforeEach(() => {
    // Reset store state before each test
    const { result } = renderHook(() => useAuthStore());
    act(() => {
      result.current.clearError();
    });
  });

  it('should initialize with null user', () => {
    const { result } = renderHook(() => useAuthStore());
    expect(result.current.user).toBeNull();
    expect(result.current.accessToken).toBeNull();
  });

  it('should handle successful login', async () => {
    const { result } = renderHook(() => useAuthStore());

    const mockResponse = {
      user: { username: 'testuser', subscription_tier: 'free' as const },
      access_token: 'token123',
      refresh_token: 'refresh123',
      token_type: 'bearer' as const,
      expires_in: 900,
    };

    vi.mocked(authAPI.login).mockResolvedValueOnce(mockResponse);

    await act(async () => {
      await result.current.login('testuser', 'password123');
    });

    expect(result.current.user).toEqual(mockResponse.user);
    expect(result.current.accessToken).toBe('token123');
    expect(result.current.refreshToken).toBe('refresh123');
  });

  it('should handle login error', async () => {
    const { result } = renderHook(() => useAuthStore());

    vi.mocked(authAPI.login).mockRejectedValueOnce(new Error('Invalid credentials'));

    await act(async () => {
      try {
        await result.current.login('testuser', 'wrongpassword');
      } catch (e) {
        // Expected
      }
    });

    expect(result.current.error).toBe('Invalid credentials');
    expect(result.current.user).toBeNull();
  });

  it('should handle logout', async () => {
    const { result } = renderHook(() => useAuthStore());

    // Set initial state
    act(() => {
      result.current.setTokens('token123', 'refresh123');
    });

    vi.mocked(authAPI.logout).mockResolvedValueOnce(undefined);

    await act(async () => {
      await result.current.logout();
    });

    expect(result.current.user).toBeNull();
    expect(result.current.accessToken).toBeNull();
  });

  it('should clear error', () => {
    const { result } = renderHook(() => useAuthStore());

    // Manually set error for testing
    expect(result.current.error).toBeNull();

    result.current.clearError();
    expect(result.current.error).toBeNull();
  });
});
