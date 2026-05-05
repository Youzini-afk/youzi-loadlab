import { useEffect, useState } from 'react';
import { Alert, Box, Button, Chip, Dialog, DialogContent, DialogTitle, MenuItem, TextField, Typography } from '@mui/material';
import { createSecret, listSecrets, listTargets } from '../api/client';
import type { Secret, Target } from '../types/api';

const KIND_OPTIONS = ['api_key', 'admin_password', 'fireworks_keys', 'bearer_token', 'cookie'];

export function SecretsPage() {
  const [secrets, setSecrets] = useState<Secret[]>([]);
  const [targets, setTargets] = useState<Target[]>([]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ name: '', kind: 'api_key', plaintext: '', target_id: '' });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listSecrets().then(setSecrets).catch(() => null);
    listTargets().then(setTargets).catch(() => null);
  }, []);

  function field(k: keyof typeof form) {
    return { value: form[k], onChange: (e: React.ChangeEvent<HTMLInputElement>) => setForm(f => ({ ...f, [k]: e.target.value })) };
  }

  async function handleCreate() {
    setSubmitting(true); setError(null);
    try {
      const s = await createSecret({ name: form.name, kind: form.kind, plaintext: form.plaintext, target_id: form.target_id || null });
      setSecrets(ss => [s, ...ss]);
      setOpen(false);
      setForm({ name: '', kind: 'api_key', plaintext: '', target_id: '' });
    } catch (e) { setError(e instanceof Error ? e.message : '创建失败'); }
    finally { setSubmitting(false); }
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h5" fontWeight={700}>Secrets</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>API Key、密码等凭证，明文仅写入时传输，之后不再返回。</Typography>
        </Box>
        <Button variant="contained" size="small" onClick={() => setOpen(true)}>+ 新建 Secret</Button>
      </Box>

      {secrets.length === 0 ? (
        <Box sx={{ py: 8, textAlign: 'center', color: 'text.secondary' }}>
          <Typography>还没有 Secret，点击右上角新建一个。</Typography>
        </Box>
      ) : (
        <Box sx={{ display: 'grid', gap: 1.5 }}>
          {secrets.map(s => {
            const target = targets.find(t => t.id === s.target_id);
            return (
              <Box key={s.id} sx={{ p: 2.5, borderRadius: 2, bgcolor: 'background.paper', border: '1px solid rgba(255,255,255,0.07)', display: 'flex', alignItems: 'center', gap: 2 }}>
                <Box sx={{ flex: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 0.5 }}>
                    <Typography fontWeight={600}>{s.name}</Typography>
                    <Chip label={s.kind} size="small" variant="outlined" sx={{ fontSize: '0.65rem', height: 18 }} />
                    {target && <Chip label={target.name} size="small" color="primary" variant="outlined" sx={{ fontSize: '0.65rem', height: 18 }} />}
                  </Box>
                  <Typography variant="body2" color="text.secondary" sx={{ fontFamily: 'monospace' }}>{s.masked}</Typography>
                </Box>
                <Typography variant="caption" color="text.disabled">fp: {s.fingerprint}</Typography>
              </Box>
            );
          })}
        </Box>
      )}

      <Dialog open={open} onClose={() => setOpen(false)} PaperProps={{ sx: { width: 440 } }}>
        <DialogTitle sx={{ fontWeight: 700 }}>新建 Secret</DialogTitle>
        <DialogContent sx={{ display: 'grid', gap: 2, pt: '8px !important' }}>
          {error && <Alert severity="error">{error}</Alert>}
          <TextField label="名称" size="small" fullWidth {...field('name')} />
          <TextField select label="类型" size="small" fullWidth {...field('kind')}>
            {KIND_OPTIONS.map(k => <MenuItem key={k} value={k}>{k}</MenuItem>)}
          </TextField>
          <TextField label="明文值" size="small" fullWidth type="password" {...field('plaintext')} />
          <TextField select label="关联 Target（可选）" size="small" fullWidth {...field('target_id')}>
            <MenuItem value="">不关联</MenuItem>
            {targets.map(t => <MenuItem key={t.id} value={t.id}>{t.name}</MenuItem>)}
          </TextField>
          <Box sx={{ display: 'flex', gap: 1.5, mt: 1 }}>
            <Button variant="outlined" onClick={() => setOpen(false)} sx={{ flex: 1 }}>取消</Button>
            <Button variant="contained" disabled={!form.name || !form.plaintext || submitting} onClick={handleCreate} sx={{ flex: 1 }}>
              {submitting ? '创建中...' : '创建'}
            </Button>
          </Box>
        </DialogContent>
      </Dialog>
    </Box>
  );
}
