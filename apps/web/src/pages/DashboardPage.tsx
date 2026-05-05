import { useState } from 'react';
import { Box, Button, Tab, Tabs, Typography } from '@mui/material';
import { LaunchDrawer } from '../components/LaunchDrawer';
import { RunDetailPage } from './RunDetailPage';
import { TargetsPage } from './TargetsPage';
import { RunsPage } from './RunsPage';
import { ScenariosTab } from './ScenariosTab';
import type { Run } from '../types/api';

type DashboardPageProps = { username: string; onLogout: () => Promise<void> };

export function DashboardPage({ username, onLogout }: DashboardPageProps) {
  const [tab, setTab] = useState(0);
  const [drawerScenario, setDrawerScenario] = useState<{ id: string; name: string } | null>(null);
  const [activeRun, setActiveRun] = useState<Run | null>(null);

  if (activeRun) {
    return <RunDetailPage run={activeRun} onBack={() => setActiveRun(null)} />;
  }

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
      {/* Header */}
      <Box sx={{ px: 4, py: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.06)', bgcolor: 'rgba(15,15,26,0.9)', backdropFilter: 'blur(8px)', position: 'sticky', top: 0, zIndex: 10 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Box sx={{ width: 30, height: 30, borderRadius: 1.5, bgcolor: 'primary.main', display: 'grid', placeItems: 'center', fontSize: 15 }}>⚡</Box>
          <Typography fontWeight={700} letterSpacing="-0.3px">YouziLoadLab</Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="body2" color="text.secondary">{username}</Typography>
          <Button onClick={onLogout} size="small" variant="outlined" sx={{ borderColor: 'rgba(255,255,255,0.15)' }}>退出</Button>
        </Box>
      </Box>

      {/* Tabs */}
      <Box sx={{ borderBottom: '1px solid rgba(255,255,255,0.06)', px: 4, bgcolor: 'rgba(15,15,26,0.6)' }}>
        <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ minHeight: 44, '& .MuiTab-root': { minHeight: 44, fontSize: '0.85rem' } }}>
          <Tab label="场景" />
          <Tab label="提供商" />
          <Tab label="历史记录" />
        </Tabs>
      </Box>

      {/* Content */}
      <Box sx={{ p: 4, maxWidth: 960, mx: 'auto' }}>
        {tab === 0 && <ScenariosTab onLaunch={(id, name) => setDrawerScenario({ id, name })} />}
        {tab === 1 && <TargetsPage />}
        {tab === 2 && <RunsPage onOpenRun={setActiveRun} />}
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
