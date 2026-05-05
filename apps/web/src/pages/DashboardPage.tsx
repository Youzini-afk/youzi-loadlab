import { useState } from 'react';
import { Box, Button, Chip, Typography } from '@mui/material';
import { LaunchDrawer } from '../components/LaunchDrawer';
import { RunDetailPage } from './RunDetailPage';
import type { Run } from '../types/api';

type Scenario = {
  id: string;
  name: string;
  description: string;
  tag: string;
  color: 'primary' | 'secondary' | 'default' | 'warning';
  status: 'ready' | 'beta' | 'soon';
};

const SCENARIOS: Scenario[] = [
  { id: 'openai-chat', name: 'OpenAI Chat Load', description: '对 OpenAI 兼容接口发起并发聊天请求，测量吞吐量与延迟分布。', tag: 'LLM', color: 'primary', status: 'ready' },
  { id: 'nashiyard-fireworks', name: 'NashiYard Fireworks', description: '模拟 NashiYard 网关高并发流量，验证限流与熔断策略。', tag: 'Gateway', color: 'secondary', status: 'ready' },
  { id: 'polling', name: 'Polling System', description: '长轮询场景压测，检测连接保持与服务端推送性能。', tag: 'Realtime', color: 'warning', status: 'beta' },
  { id: 'smoke', name: 'Smoke Check', description: '快速冒烟测试，验证所有核心端点可达性与基础响应正确性。', tag: 'Health', color: 'default', status: 'soon' },
];

const STATUS_LABEL: Record<Scenario['status'], string> = { ready: '可用', beta: 'Beta', soon: '即将上线' };

type DashboardPageProps = { username: string; onLogout: () => Promise<void> };

export function DashboardPage({ username, onLogout }: DashboardPageProps) {
  const [drawerScenario, setDrawerScenario] = useState<Scenario | null>(null);
  const [activeRun, setActiveRun] = useState<Run | null>(null);

  if (activeRun) {
    return <RunDetailPage run={activeRun} onBack={() => setActiveRun(null)} />;
  }

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default', backgroundImage: 'radial-gradient(ellipse 60% 40% at 80% 0%, rgba(34,211,238,0.1) 0%, transparent 60%)' }}>
      <Box sx={{ px: 4, py: 2.5, display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.06)', backdropFilter: 'blur(8px)', position: 'sticky', top: 0, zIndex: 10, bgcolor: 'rgba(15,15,26,0.8)' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Box sx={{ width: 32, height: 32, borderRadius: 1.5, bgcolor: 'primary.main', display: 'grid', placeItems: 'center', fontSize: 16 }}>⚡</Box>
          <Typography fontWeight={700} letterSpacing="-0.3px">YouziLoadLab</Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="body2" color="text.secondary">{username}</Typography>
          <Button onClick={onLogout} size="small" variant="outlined" sx={{ borderColor: 'rgba(255,255,255,0.15)' }}>退出</Button>
        </Box>
      </Box>

      <Box sx={{ p: 4, maxWidth: 960, mx: 'auto' }}>
        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" fontWeight={700} letterSpacing="-0.5px">场景套件</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>WebUI load testing for NashiYard and OpenAI-compatible API gateways.</Typography>
        </Box>

        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 2 }}>
          {SCENARIOS.map((s) => (
            <ScenarioCard key={s.id} scenario={s} onLaunch={() => setDrawerScenario(s)} />
          ))}
        </Box>
      </Box>

      {drawerScenario && (
        <LaunchDrawer
          open
          scenarioId={drawerScenario.id}
          scenarioName={drawerScenario.name}
          onClose={() => setDrawerScenario(null)}
          onLaunched={(run) => { setDrawerScenario(null); setActiveRun(run); }}
        />
      )}
    </Box>
  );
}

function ScenarioCard({ scenario: s, onLaunch }: { scenario: Scenario; onLaunch: () => void }) {
  const disabled = s.status === 'soon';
  return (
    <Box sx={{ p: 3, borderRadius: 2, bgcolor: 'background.paper', border: '1px solid rgba(255,255,255,0.07)', display: 'flex', flexDirection: 'column', gap: 2, opacity: disabled ? 0.5 : 1, transition: 'border-color 0.2s, box-shadow 0.2s', ...(!disabled && { cursor: 'pointer', '&:hover': { borderColor: 'primary.main', boxShadow: '0 0 0 1px rgba(99,102,241,0.3)' } }) }}>
      <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <Chip label={s.tag} color={s.color} size="small" sx={{ fontWeight: 600, fontSize: '0.7rem' }} />
        <Chip label={STATUS_LABEL[s.status]} size="small" variant="outlined" sx={{ fontSize: '0.65rem', height: 20, borderColor: 'rgba(255,255,255,0.15)', color: 'text.secondary' }} />
      </Box>
      <Box>
        <Typography fontWeight={600} sx={{ mb: 0.5 }}>{s.name}</Typography>
        <Typography variant="body2" color="text.secondary" lineHeight={1.6}>{s.description}</Typography>
      </Box>
      <Button disabled={disabled} size="small" variant={disabled ? 'outlined' : 'contained'} sx={{ alignSelf: 'flex-start', mt: 'auto' }} onClick={onLaunch}>
        {disabled ? '即将上线' : '启动测试'}
      </Button>
    </Box>
  );
}
