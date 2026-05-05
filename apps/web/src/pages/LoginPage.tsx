import { FormEvent, useState } from 'react';
import { Alert, Box, Button, Card, CardContent, TextField, Typography } from '@mui/material';

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
        bgcolor: 'grey.100',
        p: 3,
      }}
    >
      <Card sx={{ width: '100%', maxWidth: 420 }}>
        <CardContent sx={{ display: 'grid', gap: 2.5 }}>
          <Box>
            <Typography variant="h4" fontWeight={800}>
              YouziLoadLab
            </Typography>
            <Typography color="text.secondary" sx={{ mt: 1 }}>
              登录后才能配置目标、保存密钥和启动压测任务。
            </Typography>
          </Box>
          {error ? <Alert severity="error">{error}</Alert> : null}
          <Box component="form" onSubmit={handleSubmit} sx={{ display: 'grid', gap: 2 }}>
            <TextField
              autoFocus
              fullWidth
              label="管理员密码"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
            <Button disabled={!password || submitting} size="large" type="submit" variant="contained">
              {submitting ? '登录中...' : '登录'}
            </Button>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
}
