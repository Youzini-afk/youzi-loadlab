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
