import { useEffect, useState } from 'react';
import { Alert, Box, Button, Chip, Dialog, DialogContent, DialogTitle, MenuItem, TextField, Typography } from '@mui/material';
import { createTarget, listTargets } from '../api/client';
import type { Target } from '../types/api';

const KIND_LABEL: Record<string, string> = {
  nashiyard: 'NashiYard',
  openai_compatible: 'OpenAI Compatible',
  generic_http: 'Generic HTTP',
};

const SECRET_KIND_OPTIONS = ['api_key', 'admin_password', 'bearer_token', 'cookie'];

type Form = {
  name: string; kind: string; base_url: string;
  default_model: string; admin_username: string;
  secret_name: string; secret_kind: string; secret_plaintext: string;
};

const EMPTY: Form = {
  name: '', kind: 'openai_compatible', base_url: '',
  default_model: '', admin_username: '',
  secret_name: 'API Key', secret_kind: 'api_key', secret_plaintext: '',
};

export function TargetsPage() {
  const [targets, setTargets] = useState<Target[]>([]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<Form>(EMPTY);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { listTargets().then(setTargets).catch(() => null); }, []);

  function f(k: keyof Form) {
    return { value: form[k], onChange: (e: React.ChangeEvent<HTMLInputElement>) => setForm(v => ({ ...v, [k]: e.target.value })) };
  }

  async function handleCreate() {
    setSubmitting(true); setError(null);
    try {
      const t = await createTarget({
        name: form.name, kind: form.kind, base_url: form.base_url,
        admin_username: form.admin_username || null,
        default_model: form.default_model || null,
        secret: form.secret_plaintext
          ? { name: form.secret_name, kind: form.secret_kind, plaintext: form.secret_plaintext }
          : null,
      });
      setTargets(ts => [t, ...ts]);
      setOpen(false); setForm(EMPTY);
    } catch (e) { setError(e instanceof Error ? e.message : '创建失败'); }
    finally { setSubmitting(false); }
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h5" fontWeight={700}>提供商</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>被测服务的地址与凭证，一次配置完成。</Typography>
        </Box>
        <Button variant="contained" size="small" onClick={() => setOpen(true)}>+ 新建提供商</Button>
      </Box>

      {targets.length === 0 ? (
        <Box sx={{ py: 8, textAlign: 'center', color: 'text.secondary' }}>
          <Typography>还没有提供商，点击右上角新建一个。</Typography>
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

      <Dialog open={open} onClose={() => setOpen(false)} PaperProps={{ sx: { width: 460 } }}>
        <DialogTitle sx={{ fontWeight: 700 }}>新建提供商</DialogTitle>
        <DialogContent sx={{ display: 'grid', gap: 2, pt: '8px !important' }}>
          {error && <Alert severity="error">{error}</Alert>}

          <TextField label="名称" size="small" fullWidth {...f('name')} placeholder="My OpenAI" />
          <TextField select label="类型" size="small" fullWidth {...f('kind')}>
            {Object.entries(KIND_LABEL).map(([v, l]) => <MenuItem key={v} value={v}>{l}</MenuItem>)}
          </TextField>
          <TextField label="Base URL" size="small" fullWidth placeholder="https://api.openai.com/v1" {...f('base_url')} />
          <TextField label="默认模型（可选）" size="small" fullWidth placeholder="gpt-4o" {...f('default_model')} />

          <Box sx={{ pt: 1, borderTop: '1px solid rgba(255,255,255,0.08)' }}>
            <Typography variant="caption" color="text.secondary" sx={{ mb: 1.5, display: 'block' }}>API 凭证（可选）</Typography>
            <Box sx={{ display: 'grid', gap: 2 }}>
              <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1.5 }}>
                <TextField label="凭证名称" size="small" {...f('secret_name')} />
                <TextField select label="凭证类型" size="small" {...f('secret_kind')}>
                  {SECRET_KIND_OPTIONS.map(k => <MenuItem key={k} value={k}>{k}</MenuItem>)}
                </TextField>
              </Box>
              <TextField label="密钥值" size="small" fullWidth type="password" placeholder="sk-..." {...f('secret_plaintext')} />
            </Box>
          </Box>

          <Box sx={{ display: 'flex', gap: 1.5, mt: 0.5 }}>
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
