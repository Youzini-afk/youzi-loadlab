import { Box, Button, Chip, Typography } from '@mui/material';

type Scenario = { id: string; name: string; description: string; tag: string; color: 'primary' | 'secondary' | 'default' | 'warning'; status: 'ready' | 'beta' | 'soon' };

const SCENARIOS: Scenario[] = [
  { id: 'openai-chat', name: 'OpenAI Chat Load', description: '对 OpenAI 兼容接口发起并发聊天请求，测量吞吐量与延迟分布。', tag: 'LLM', color: 'primary', status: 'ready' },
  { id: 'nashiyard-fireworks', name: 'NashiYard Fireworks', description: '模拟 NashiYard 网关高并发流量，验证限流与熔断策略。', tag: 'Gateway', color: 'secondary', status: 'ready' },
  { id: 'polling', name: 'Polling System', description: '长轮询场景压测，检测连接保持与服务端推送性能。', tag: 'Realtime', color: 'warning', status: 'beta' },
  { id: 'smoke', name: 'Smoke Check', description: '快速冒烟测试，验证所有核心端点可达性与基础响应正确性。', tag: 'Health', color: 'default', status: 'soon' },
];

const STATUS_LABEL: Record<Scenario['status'], string> = { ready: '可用', beta: 'Beta', soon: '即将上线' };

type Props = { onLaunch: (id: string, name: string) => void };

export function ScenariosTab({ onLaunch }: Props) {
  return (
    <Box>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h5" fontWeight={700} letterSpacing="-0.5px">场景套件</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>WebUI load testing for NashiYard and OpenAI-compatible API gateways.</Typography>
      </Box>
      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 2 }}>
        {SCENARIOS.map((s) => {
          const disabled = s.status === 'soon';
          return (
            <Box key={s.id} sx={{ p: 3, borderRadius: 2, bgcolor: 'background.paper', border: '1px solid rgba(255,255,255,0.07)', display: 'flex', flexDirection: 'column', gap: 2, opacity: disabled ? 0.5 : 1, transition: 'border-color 0.2s', ...(!disabled && { '&:hover': { borderColor: 'primary.main' } }) }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Chip label={s.tag} color={s.color} size="small" sx={{ fontWeight: 600, fontSize: '0.7rem' }} />
                <Chip label={STATUS_LABEL[s.status]} size="small" variant="outlined" sx={{ fontSize: '0.65rem', height: 20, borderColor: 'rgba(255,255,255,0.15)', color: 'text.secondary' }} />
              </Box>
              <Box>
                <Typography fontWeight={600} sx={{ mb: 0.5 }}>{s.name}</Typography>
                <Typography variant="body2" color="text.secondary" lineHeight={1.6}>{s.description}</Typography>
              </Box>
              <Button disabled={disabled} size="small" variant={disabled ? 'outlined' : 'contained'} sx={{ alignSelf: 'flex-start', mt: 'auto' }} onClick={() => onLaunch(s.id, s.name)}>
                {disabled ? '即将上线' : '启动测试'}
              </Button>
            </Box>
          );
        })}
      </Box>
    </Box>
  );
}
