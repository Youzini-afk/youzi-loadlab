import type { AuthStatus, HealthResponse } from '../types/api';

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch('/api/health');
  if (!response.ok) {
    throw new Error(`Health request failed: ${response.status}`);
  }
  return response.json() as Promise<HealthResponse>;
}

export async function getMe(): Promise<AuthStatus> {
  const response = await fetch('/api/auth/me');
  if (response.status === 401) {
    return { authenticated: false, user: null };
  }
  if (!response.ok) {
    throw new Error(`Auth status request failed: ${response.status}`);
  }
  return response.json() as Promise<AuthStatus>;
}

export async function login(password: string): Promise<AuthStatus> {
  const response = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ password }),
  });
  if (response.status === 401) {
    throw new Error('密码不正确');
  }
  if (!response.ok) {
    throw new Error(`Login failed: ${response.status}`);
  }
  return response.json() as Promise<AuthStatus>;
}

export async function logout(): Promise<AuthStatus> {
  const response = await fetch('/api/auth/logout', { method: 'POST' });
  if (!response.ok) {
    throw new Error(`Logout failed: ${response.status}`);
  }
  return response.json() as Promise<AuthStatus>;
}
