export type HealthResponse = {
  status: string;
  app: string;
  environment: string;
  timestamp: string;
};

export type AuthUser = {
  username: string;
};

export type AuthStatus = {
  authenticated: boolean;
  user: AuthUser | null;
};

export type Target = {
  id: string;
  name: string;
  kind: string;
  base_url: string;
  admin_username: string | null;
  default_model: string | null;
};

export type Scenario = {
  id: string;
  title: string;
  description: string;
  version: string;
  schema_json: Record<string, unknown>;
  enabled: boolean;
};

export type Run = {
  id: string;
  name: string;
  target_id: string;
  scenario_id: string;
  status: string;
  config_json: Record<string, unknown>;
  locust_web_url: string | null;
  pid: number | null;
  workdir: string | null;
  command_json: string[];
  artifacts_json: Record<string, unknown>;
  exit_code: number | null;
  error_message: string | null;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
};

export type RunEvent = {
  id: number;
  run_id: string;
  level: string;
  event_type: string;
  message: string;
  payload_json: Record<string, unknown>;
  created_at: string;
};

export type Secret = {
  id: string;
  target_id: string | null;
  name: string;
  kind: string;
  fingerprint: string;
  masked: string;
};

export type RunMetrics = {
  id: number;
  run_id: string;
  timestamp: string;
  requests_total: number;
  failures_total: number;
  current_rps: number;
  avg_latency_ms: number;
  p50_latency_ms: number;
  p90_latency_ms: number;
  p95_latency_ms: number;
  p99_latency_ms: number;
  status_counts_json: Record<string, unknown>;
  error_counts_json: Record<string, unknown>;
  tokens_total: number;
};

export type Report = {
  id: string;
  run_id: string;
  summary_json: Record<string, unknown>;
  markdown: string;
};
