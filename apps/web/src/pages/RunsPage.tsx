import { useEffect, useState } from 'react';
import { Box, Button, Chip, Typography } from '@mui/material';
import { listRuns } from '../api/client';
import type { Run } from '../types/api';

const STATUS_COLOR: Record<string, 'default' | 'primary' | 'success' | 'error' | 'warning'> = {
  created: 'default', running: 'primary', finished: 'success', failed: 'error', stopping: 'warning',
};

type Props = { onOpenRun: (run: Run) => void };

export function RunsPage({ onOpenRun }: Props) {
  const [runs, setRuns] = useState<Run[]>([]);

  useEffect(() => { listRuns().then(setRuns).catch(() => null); }, []);

  return (
    <Box>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h5" fontWeight={700}>历史记录</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>所有压测任务的运行记录。</Typography>
      </Box>

      {runs.length === 0 ? (
        <Box sx={{ py: 8, textAlign: 'center', color: 'text.secondary' }}>
          <Typography>还没有运行记录，去场景页启动一个测试吧。</Typography>
        </Box>
      ) : (
        <Box sx={{ display: 'grid', gap: 1.5 }}>
          {runs.map(r => (
            <Box key={r.id} sx={{ p: 2.5, borderRadius: 2, bgcolor: 'background.paper', border: '1px solid rgba(255,255,255,0.07)', display: 'flex', alignItems: 'center', gap: 2 }}>
              <Box sx={{ flex: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 0.5 }}>
                  <Typography fontWeight={600}>{r.name}</Typography>
                  <Chip label={r.status} color={STATUS_COLOR[r.status] ?? 'default'} size="small" sx={{ fontSize: '0.65rem', height: 20 }} />
                </Box>
                <Typography variant="caption" color="text.secondary">
                  {r.scenario_id} · {new Date(r.created_at).toLocaleString()}
                </Typography>
                {r.error_message && <Typography variant="caption" color="error.main" sx={{ display: 'block' }}>{r.error_message}</Typography>}
              </Box>
              <Button size="small" variant="outlined" onClick={() => onOpenRun(r)}>查看详情</Button>
            </Box>
          ))}
        </Box>
      )}
    </Box>
  );
}
