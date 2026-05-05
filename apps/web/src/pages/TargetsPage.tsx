import { useEffect, useState } from 'react';
import { Alert, Box, Button, Chip, Dialog, DialogContent, DialogTitle, MenuItem, TextField, Typography } from '@mui/material';
import { createTarget, listTargets } from '../api/client';
import type { Target } from '../types/api';

const KIND_LABEL: Record<string, string> = { nashiyard: 'NashiYard', openai_compatible: 'OpenAI Compatible', generic_http: 'Generic HTTP' };

export function TargetsPage() {
  const [targets, setTargets] = useState<Target[]>([]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ name: '', kind: 'openai_compatible', base_url: '', admin_username: '', default_model: '' });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { listTargets().then(setTargets).catch(() => null); }, []);

  function field(k: keyof typeof form) {
    return { value: form[k], onChange: (e: React.ChangeEvent<HTMLInputElement>) => setForm(f => ({ ...f, [k]: e.target.value })) };
  }

  async function handleCreate() {
    setSubmitting(true); setError(null);
    try {
      const t = await createTarget({ name: form.name, kind: form.kind, base_url: form.base_url, admin_username: form.admin_username || null, default_model: form.default_model || null });
      setTargets(ts => [t, ...ts]);
      setOpen(false);
      setForm({ name: '', kind: 'openai_compatible', base_url: '', admin_username: '', default_model: '' });
    } catch (e) { setError(e instanceof Error ? e.message : '创建失败'); }
    finally { setSubmitting(false); }
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h5" fontWeight={700}>Targets</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>被测服务的地址与配置。</Typography>
        </Box>
        <Button variant="contained" size="small" onClick={() => setOpen(true)}>+ 新建 Target</Button>
      </Box>

      {targets.length === 0 ? (
        <Box sx={{ py: 8, textAlign: 'center', color: 'text.secondary' }}>
          <Typography>还没有 Target，点击右上角新建一个。</Typography>
        </Box>
      ) : (
        <Box sx={{ display: 'grid', gap: 1.5 }}>
          {targets.map(t => (
            <Box key={t.id} sx={{ p: 2.5, borderRadius: 2, bgcolor: 'background.paper', border: '1px solid rgba(255,255,255,0.07)', display: 'flex', alignItems: 'center', gap: 2 }}>
              <Box sx={{ flex: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 0.5 }}>
                  <Typography fontWeight={600}>{t.name}</Typography>
                  <Chip label={KIND_LABEL[t.kind] ?? t.kind} size="small" variant="outlined" sx={{ fontSize: '0.65rem', height: 18 }} />
                </Box>
                <Typography variant="body2" color="text.secondary">{t.base_url}</Typography>
                {t.default_model && <Typography variant="caption" color="text.disabled">model: {t.default_model}</Typography>}
              </Box>
            </Box>
          ))}
        </Box>
      )}

      <Dialog open={open} onClose={() => setOpen(false)} PaperProps={{ sx: { width: 440 } }}>
        <DialogTitle sx={{ fontWeight: 700 }}>新建 Target</DialogTitle>
        <DialogContent sx={{ display: 'grid', gap: 2, pt: '8px !important' }}>
          {error && <Alert severity="error">{error}</Alert>}
          <TextField label="名称" size="small" fullWidth {...field('name')} />
          <TextField select label="类型" size="small" fullWidth {...field('kind')}>
            {Object.entries(KIND_LABEL).map(([v, l]) => <MenuItem key={v} value={v}>{l}</MenuItem>)}
          </TextField>
          <TextField label="Base URL" size="small" fullWidth placeholder="https://api.example.com" {...field('base_url')} />
          <TextField label="Admin Username（可选）" size="small" fullWidth {...field('admin_username')} />
          <TextField label="Default Model（可选）" size="small" fullWidth placeholder="gpt-4o" {...field('default_model')} />
          <Box sx={{ display: 'flex', gap: 1.5, mt: 1 }}>
            <Button variant="outlined" onClick={() => setOpen(false)} sx={{ flex: 1 }}>取消</Button>
            <Button variant="contained" disabled={!form.name || !form.base_url || submitting} onClick={handleCreate} sx={{ flex: 1 }}>
              {submitting ? '创建中...' : '创建'}
            </Button>
          </Box>
        </DialogContent>
      </Dialog>
    </Box>
  );
}
