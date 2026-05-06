import { useEffect, useState } from 'react';
import { Alert, Box, Button, Chip, Typography } from '@mui/material';
import { listScenarios } from '../api/client';
import type { Scenario } from '../types/api';

type ScenarioCard = Scenario & {
  tag: string;
  color: 'primary' | 'secondary' | 'default' | 'warning';
  status: 'ready' | 'beta' | 'soon';
};

const STATUS_LABEL: Record<ScenarioCard['status'], string> = { ready: '可用', beta: 'Beta', soon: '即将上线' };

type Props = { onLaunch: (id: string, name: string) => void };

export function ScenariosTab({ onLaunch }: Props) {
  const [scenarios, setScenarios] = useState<ScenarioCard[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listScenarios()
      .then((items) => setScenarios(items.map(toScenarioCard)))
      .catch((caught) => setError(caught instanceof Error ? caught.message : '场景加载失败'));
  }, []);

  return (
    <Box>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h5" fontWeight={700} letterSpacing="-0.5px">场景套件</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>WebUI load testing for NashiYard and OpenAI-compatible API gateways.</Typography>
      </Box>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 2 }}>
        {scenarios.map((s) => {
          const disabled = s.status === 'soon';
          return (
            <Box key={s.id} sx={{ p: 3, borderRadius: 2, bgcolor: 'background.paper', border: '1px solid rgba(255,255,255,0.07)', display: 'flex', flexDirection: 'column', gap: 2, opacity: disabled ? 0.5 : 1, transition: 'border-color 0.2s', ...(!disabled && { '&:hover': { borderColor: 'primary.main' } }) }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Chip label={s.tag} color={s.color} size="small" sx={{ fontWeight: 600, fontSize: '0.7rem' }} />
                <Chip label={STATUS_LABEL[s.status]} size="small" variant="outlined" sx={{ fontSize: '0.65rem', height: 20, borderColor: 'rgba(255,255,255,0.15)', color: 'text.secondary' }} />
              </Box>
              <Box>
                <Typography fontWeight={600} sx={{ mb: 0.5 }}>{s.title}</Typography>
                <Typography variant="body2" color="text.secondary" lineHeight={1.6}>{s.description}</Typography>
              </Box>
              <Button disabled={disabled} size="small" variant={disabled ? 'outlined' : 'contained'} sx={{ alignSelf: 'flex-start', mt: 'auto' }} onClick={() => onLaunch(s.id, s.title)}>
                {disabled ? '即将上线' : '启动测试'}
              </Button>
            </Box>
          );
        })}
      </Box>
    </Box>
  );
}

function toScenarioCard(scenario: Scenario): ScenarioCard {
  if (scenario.id === 'nashiyard-fireworks-channel') {
    return { ...scenario, tag: 'Gateway', color: 'secondary', status: 'ready' };
  }
  if (scenario.id === 'nashiyard-polling-system') {
    return { ...scenario, tag: 'Polling', color: 'warning', status: 'beta' };
  }
  if (scenario.id === 'smoke-check') {
    return { ...scenario, tag: 'Health', color: 'default', status: 'ready' };
  }
  return { ...scenario, tag: 'LLM', color: 'primary', status: 'ready' };
}
