import { useEffect, useState } from 'react';
import { CssBaseline, ThemeProvider, createTheme } from '@mui/material';

import { getMe, login, logout } from './api/client';
import { DashboardPage } from './pages/DashboardPage';
import { LoginPage } from './pages/LoginPage';
import type { AuthUser } from './types/api';

const theme = createTheme({ palette: { mode: 'light' } });

export default function App() {
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState<AuthUser | null>(null);

  useEffect(() => {
    getMe()
      .then((status) => setUser(status.user))
      .finally(() => setLoading(false));
  }, []);

  async function handleLogin(password: string) {
    const status = await login(password);
    setUser(status.user);
  }

  async function handleLogout() {
    await logout();
    setUser(null);
  }

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      {loading ? null : user ? (
        <DashboardPage username={user.username} onLogout={handleLogout} />
      ) : (
        <LoginPage onLogin={handleLogin} />
      )}
    </ThemeProvider>
  );
}
