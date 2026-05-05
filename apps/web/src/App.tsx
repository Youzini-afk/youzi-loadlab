import { CssBaseline, ThemeProvider, createTheme } from '@mui/material';

import { DashboardPage } from './pages/DashboardPage';

const theme = createTheme({ palette: { mode: 'light' } });

export default function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <DashboardPage />
    </ThemeProvider>
  );
}
