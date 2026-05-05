import { useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Drawer,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  TextField,
  Typography,
} from '@mui/material';
import { createRun, listTargets } from '../api/client';
import type { Run, Target } from '../types/api';

type Props = {
  scenarioId: string;
  scenarioName: string;
  open: boolean;
  onClose: () => void;
  onLaunched: (run: Run) => void;
};

export function LaunchDrawer({ scenarioId, scenarioName, open, onClose, onLaunched }: Props) {
  const [targets, setTargets] = useState<Target[]>([]);
  const [targetId, setTargetId] = useState('');
  const [runName, setRunName] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      listTargets().then(setTargets).catch(() => null);
      setError(null);
    }
  }, [open]);

  async function handleSubmit() {
    if (!targetId || !runName) return;
    setSubmitting(true);
    setError(null);
    try {
      const run = await createRun({
        name: runName,
        target_id: targetId,
        scenario_id: scenarioId,
        config_json: {},
      });
      onLaunched(run);
    } catch (e) {
      setError(e instanceof Error ? e.message : '启动失败');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Drawer anchor="right" open={open} onClose={onClose} PaperProps={{ sx: { width: 400, p: 3 } }}>
      <Typography variant="h6" fontWeight={700} mb={0.5}>
        启动测试
      </Typography>
      <Typography variant="body2" color="text.secondary" mb={3}>
        {scenarioName}
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Box sx={{ display: 'grid', gap: 2.5 }}>
        <TextField
          label="运行名称"
          size="small"
          fullWidth
          value={runName}
          onChange={(e) => setRunName(e.target.value)}
          placeholder={`${scenarioName} - ${new Date().toLocaleDateString()}`}
        />

        <FormControl size="small" fullWidth>
          <InputLabel>目标 Target</InputLabel>
          <Select value={targetId} label="目标 Target" onChange={(e) => setTargetId(e.target.value)}>
            {targets.length === 0 && (
              <MenuItem disabled value="">
                暂无 Target，请先创建
              </MenuItem>
            )}
            {targets.map((t) => (
              <MenuItem key={t.id} value={t.id}>
                <Box>
                  <Typography variant="body2" fontWeight={600}>{t.name}</Typography>
                  <Typography variant="caption" color="text.secondary">{t.base_url}</Typography>
                </Box>
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        {targets.length === 0 && (
          <Alert severity="warning" sx={{ fontSize: '0.75rem' }}>
            需要先在 Targets 页面创建一个测试目标。
          </Alert>
        )}

        <Box sx={{ display: 'flex', gap: 1.5, mt: 1 }}>
          <Button variant="outlined" onClick={onClose} sx={{ flex: 1 }}>
            取消
          </Button>
          <Button
            variant="contained"
            disabled={!targetId || !runName || submitting}
            onClick={handleSubmit}
            sx={{ flex: 1 }}
          >
            {submitting ? '启动中...' : '启动'}
          </Button>
        </Box>
      </Box>
    </Drawer>
  );
}
