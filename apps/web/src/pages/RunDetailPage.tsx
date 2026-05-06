import { useEffect, useRef, useState } from 'react';
import { Alert, Box, Button, Chip, Typography } from '@mui/material';
import { getRun, getRunEvents, getRunMetrics, getRunReport, startRun, stopRun } from '../api/client';
import type { Report, Run, RunEvent, RunMetrics } from '../types/api';

const STATUS_COLOR: Record<string, 'default' | 'primary' | 'success' | 'error' | 'warning'> = {
  created: 'default',
  running: 'primary',
  completed: 'success',
  stopped: 'warning',
  failed: 'error',
  stopping: 'warning',
};

const LEVEL_COLOR: Record<string, string> = {
  info: '#6366f1',
  warn: '#f59e0b',
  error: '#ef4444',
  debug: '#6b7280',
};

type Props = { run: Run; onBack: () => void };

export function RunDetailPage({ run: initialRun, onBack }: Props) {
  const [run, setRun] = useState(initialRun);
  const [events, setEvents] = useState<RunEvent[]>([]);
  const [metrics, setMetrics] = useState<RunMetrics[]>([]);
  const [report, setReport] = useState<Report | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const logRef = useRef<HTMLDivElement>(null);
  const polling = run.status === 'created' || run.status === 'running' || run.status === 'stopping';

  useEffect(() => {
    let active = true;
    async function poll() {
      try {
        const [r, evs, mets] = await Promise.all([
          getRun(run.id),
          getRunEvents(run.id),
          getRunMetrics(run.id),
        ]);
        if (!active) return;
        setRun(r);
        setEvents(evs);
        setMetrics(mets);
      } catch {
        // ignore transient errors
      }
    }
    poll();
    if (!polling) return;
    const id = setInterval(poll, 2000);
    return () => { active = false; clearInterval(id); };
  }, [run.id, polling]);

  // auto-scroll log
  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [events]);

  const latest = metrics[metrics.length - 1];

  async function handleStart() {
    setActionError(null);
    try {
      setRun(await startRun(run.id));
    } catch (caught) {
      setActionError(caught instanceof Error ? caught.message : '启动失败');
    }
  }

  async function handleStop() {
    setActionError(null);
    try {
      setRun(await stopRun(run.id));
    } catch (caught) {
      setActionError(caught instanceof Error ? caught.message : '停止失败');
    }
  }

  async function handleReport() {
    setActionError(null);
    try {
      setReport(await getRunReport(run.id));
    } catch (caught) {
      setActionError(caught instanceof Error ? caught.message : '报告生成失败');
    }
  }

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default', p: 4, maxWidth: 960, mx: 'auto' }}>
      <Button size="small" onClick={onBack} sx={{ mb: 2, color: 'text.secondary' }}>
        ← 返回
      </Button>

      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <Box sx={{ flex: 1 }}>
          <Typography variant="h5" fontWeight={700}>{run.name}</Typography>
          <Typography variant="body2" color="text.secondary">{run.scenario_id}</Typography>
        </Box>
        <Chip label={run.status} color={STATUS_COLOR[run.status] ?? 'default'} />
      </Box>

      {run.error_message && <Alert severity="error" sx={{ mb: 2 }}>{run.error_message}</Alert>}
      {actionError && <Alert severity="error" sx={{ mb: 2 }}>{actionError}</Alert>}

      <Box sx={{ display: 'flex', gap: 1.5, mb: 3 }}>
        <Button disabled={run.status !== 'created'} variant="contained" onClick={handleStart}>
          启动
        </Button>
        <Button disabled={!['running', 'preparing', 'stopping'].includes(run.status)} variant="outlined" onClick={handleStop}>
          停止
        </Button>
        <Button variant="outlined" onClick={handleReport}>
          生成报告
        </Button>
      </Box>

      {/* Metrics */}
      {latest && (
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 1.5, mb: 3 }}>
          {[
            { label: 'RPS', value: latest.current_rps.toFixed(1) },
            { label: '平均延迟', value: `${latest.avg_latency_ms.toFixed(0)}ms` },
            { label: 'P99', value: `${latest.p99_latency_ms.toFixed(0)}ms` },
            { label: '失败率', value: latest.requests_total > 0 ? `${((latest.failures_total / latest.requests_total) * 100).toFixed(1)}%` : '—' },
          ].map((m) => (
            <Box key={m.label} sx={{ p: 2, borderRadius: 2, bgcolor: 'background.paper', border: '1px solid rgba(255,255,255,0.07)' }}>
              <Typography variant="caption" color="text.secondary">{m.label}</Typography>
              <Typography variant="h6" fontWeight={700}>{m.value}</Typography>
            </Box>
          ))}
        </Box>
      )}

      {/* Log */}
      <Box sx={{ borderRadius: 2, bgcolor: 'background.paper', border: '1px solid rgba(255,255,255,0.07)', overflow: 'hidden' }}>
        <Box sx={{ px: 2, py: 1.5, borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
          <Typography variant="body2" fontWeight={600}>运行日志</Typography>
        </Box>
        <Box
          ref={logRef}
          sx={{ height: 360, overflowY: 'auto', p: 2, fontFamily: 'monospace', fontSize: '0.75rem', lineHeight: 1.8 }}
        >
          {events.length === 0 ? (
            <Typography variant="caption" color="text.secondary">
              {polling ? '等待日志...' : '无日志记录'}
            </Typography>
          ) : (
            events.map((e) => (
              <Box key={e.id} sx={{ display: 'flex', gap: 2 }}>
                <Box component="span" sx={{ color: 'text.disabled', flexShrink: 0 }}>
                  {new Date(e.created_at).toLocaleTimeString()}
                </Box>
                <Box component="span" sx={{ color: LEVEL_COLOR[e.level] ?? '#fff', flexShrink: 0, width: 40 }}>
                  {e.level.toUpperCase()}
                </Box>
                <Box component="span" sx={{ color: 'text.primary', wordBreak: 'break-all' }}>
                  {e.message}
                </Box>
              </Box>
            ))
          )}
        </Box>
      </Box>

      {run.locust_web_url && (
        <Box sx={{ mt: 2 }}>
          <Button variant="outlined" size="small" href={run.locust_web_url} target="_blank">
            打开 Locust Web UI
          </Button>
        </Box>
      )}

      {report && (
        <Box sx={{ mt: 2, borderRadius: 2, bgcolor: 'background.paper', border: '1px solid rgba(255,255,255,0.07)', p: 2 }}>
          <Typography variant="body2" fontWeight={600} sx={{ mb: 1 }}>报告预览</Typography>
          <Box component="pre" sx={{ m: 0, whiteSpace: 'pre-wrap', fontSize: '0.75rem', color: 'text.secondary' }}>
            {report.markdown}
          </Box>
        </Box>
      )}
    </Box>
  );
}
