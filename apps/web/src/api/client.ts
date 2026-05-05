import type { AuthStatus, HealthResponse, Run, RunEvent, RunMetrics, Scenario, Secret, Target } from '../types/api';

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) throw new Error(`${res.status}`);
  return res.json() as Promise<T>;
}

export async function getHealth(): Promise<HealthResponse> {
  return request('/api/health');
}

export async function getMe(): Promise<AuthStatus> {
  const res = await fetch('/api/auth/me');
  if (res.status === 401) return { authenticated: false, user: null };
  if (!res.ok) throw new Error(`${res.status}`);
  return res.json() as Promise<AuthStatus>;
}

export async function login(password: string): Promise<AuthStatus> {
  const res = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ password }),
  });
  if (res.status === 401) throw new Error('密码不正确');
  if (!res.ok) throw new Error(`${res.status}`);
  return res.json() as Promise<AuthStatus>;
}

export async function logout(): Promise<AuthStatus> {
  return request('/api/auth/logout', { method: 'POST' });
}

export async function listTargets(): Promise<Target[]> {
  return request('/api/targets');
}

export async function createTarget(payload: Omit<Target, 'id'>): Promise<Target> {
  return request('/api/targets', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

export async function listScenarios(): Promise<Scenario[]> {
  return request('/api/scenarios');
}

export async function createRun(payload: {
  name: string;
  target_id: string;
  scenario_id: string;
  config_json: Record<string, unknown>;
}): Promise<Run> {
  return request('/api/runs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

export async function listRuns(): Promise<Run[]> {
  return request('/api/runs');
}

export async function getRun(id: string): Promise<Run> {
  return request(`/api/runs/${id}`);
}

export async function getRunEvents(id: string): Promise<RunEvent[]> {
  return request(`/api/runs/${id}/events`);
}

export async function getRunMetrics(id: string): Promise<RunMetrics[]> {
  return request(`/api/runs/${id}/metrics`);
}

export async function listSecrets(): Promise<Secret[]> {
  return request('/api/secrets');
}

export async function createSecret(payload: {
  target_id: string | null;
  name: string;
  kind: string;
  plaintext: string;
}): Promise<Secret> {
  return request('/api/secrets', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}
