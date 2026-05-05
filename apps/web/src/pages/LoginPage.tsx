import { FormEvent, useState } from 'react';
import { Alert, Box, Button, TextField, Typography } from '@mui/material';

type LoginPageProps = {
  onLogin: (password: string) => Promise<void>;
};

export function LoginPage({ onLogin }: LoginPageProps) {
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await onLogin(password);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : '登录失败');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'grid',
        placeItems: 'center',
        bgcolor: 'background.default',
        backgroundImage:
          'radial-gradient(ellipse 80% 60% at 50% -10%, rgba(99,102,241,0.25) 0%, transparent 70%)',
        p: 3,
      }}
    >
      <Box
        sx={{
          width: '100%',
          maxWidth: 400,
          p: 4,
          borderRadius: 3,
          bgcolor: 'background.paper',
          border: '1px solid',
          borderColor: 'rgba(255,255,255,0.08)',
          boxShadow: '0 24px 48px rgba(0,0,0,0.4)',
        }}
      >
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1 }}>
            <Box
              sx={{
                width: 36,
                height: 36,
                borderRadius: 2,
                bgcolor: 'primary.main',
                display: 'grid',
                placeItems: 'center',
                fontSize: 18,
              }}
            >
              ⚡
            </Box>
            <Typography variant="h5" fontWeight={700} letterSpacing="-0.5px">
              YouziLoadLab
            </Typography>
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1.5 }}>
            登录后才能配置目标、保存密钥和启动压测任务。
          </Typography>
        </Box>

        {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}

        <Box component="form" onSubmit={handleSubmit} sx={{ display: 'grid', gap: 2 }}>
          <TextField
            autoFocus
            fullWidth
            label="管理员密码"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            size="small"
          />
          <Button
            disabled={!password || submitting}
            fullWidth
            size="large"
            type="submit"
            variant="contained"
            sx={{ mt: 0.5, py: 1.25, fontWeight: 600 }}
          >
            {submitting ? '登录中...' : '登录'}
          </Button>
        </Box>
      </Box>
    </Box>
  );
}
