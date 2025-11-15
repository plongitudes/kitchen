import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { AuthProvider, useAuth } from '../../../context/AuthContext';
import * as api from '../../../services/api';

// Mock the API module
vi.mock('../../../services/api', () => ({
  authAPI: {
    getCurrentUser: vi.fn(),
    login: vi.fn(),
    register: vi.fn(),
  },
}));

describe('AuthContext', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('initializes with no user when no token in localStorage', async () => {
    api.authAPI.getCurrentUser.mockResolvedValue({ data: null });

    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.user).toBeNull();
  });

  it('checks auth on mount if token exists', async () => {
    const mockUser = { id: '123', username: 'testuser' };
    localStorage.setItem('access_token', 'fake-token');
    api.authAPI.getCurrentUser.mockResolvedValue({ data: mockUser });

    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(api.authAPI.getCurrentUser).toHaveBeenCalled();
    expect(result.current.user).toEqual(mockUser);
  });

  it('handles successful login', async () => {
    const mockUser = { id: '123', username: 'testuser' };
    api.authAPI.login.mockResolvedValue({
      data: { access_token: 'new-token', token_type: 'bearer' },
    });
    api.authAPI.getCurrentUser.mockResolvedValue({ data: mockUser });

    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    let loginResult;
    await act(async () => {
      loginResult = await result.current.login('testuser', 'password123');
    });

    expect(loginResult.success).toBe(true);
    expect(localStorage.getItem('access_token')).toBe('new-token');
    expect(result.current.user).toEqual(mockUser);
  });

  it('handles failed login', async () => {
    api.authAPI.login.mockRejectedValue({
      response: { data: { detail: 'Invalid credentials' } },
    });

    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    let loginResult;
    await act(async () => {
      loginResult = await result.current.login('testuser', 'wrongpass');
    });

    expect(loginResult.success).toBe(false);
    expect(loginResult.error).toBe('Invalid credentials');
    expect(result.current.user).toBeNull();
  });

  it('handles successful registration', async () => {
    const mockUser = { id: '123', username: 'newuser' };
    api.authAPI.register.mockResolvedValue({ data: mockUser });
    api.authAPI.login.mockResolvedValue({
      data: { access_token: 'new-token', token_type: 'bearer' },
    });
    api.authAPI.getCurrentUser.mockResolvedValue({ data: mockUser });

    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    let registerResult;
    await act(async () => {
      registerResult = await result.current.register('newuser', 'password123');
    });

    expect(registerResult.success).toBe(true);
    expect(api.authAPI.register).toHaveBeenCalledWith('newuser', 'password123');
    expect(result.current.user).toEqual(mockUser);
  });

  it('handles logout', async () => {
    const mockUser = { id: '123', username: 'testuser' };
    localStorage.setItem('access_token', 'fake-token');
    api.authAPI.getCurrentUser.mockResolvedValue({ data: mockUser });

    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    await waitFor(() => {
      expect(result.current.user).toEqual(mockUser);
    });

    act(() => {
      result.current.logout();
    });

    expect(localStorage.getItem('access_token')).toBeNull();
    expect(result.current.user).toBeNull();
  });

  it('throws error when useAuth is used outside provider', () => {
    expect(() => {
      renderHook(() => useAuth());
    }).toThrow('useAuth must be used within an AuthProvider');
  });
});
