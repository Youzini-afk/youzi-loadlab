import { Box, Card, CardContent, Chip, Typography } from '@mui/material';

export function DashboardPage() {
  return (
    <Box sx={{ p: 4, display: 'grid', gap: 2 }}>
      <Typography variant="h4" fontWeight={700}>
        YouziLoadLab
      </Typography>
      <Typography color="text.secondary">
        WebUI load testing for NashiYard and OpenAI-compatible API gateways.
      </Typography>
      <Card>
        <CardContent>
          <Typography variant="h6">V1 Scenario Suites</Typography>
          <Box sx={{ display: 'flex', gap: 1, mt: 2, flexWrap: 'wrap' }}>
            <Chip label="OpenAI Chat Load" color="primary" />
            <Chip label="NashiYard Fireworks" color="secondary" />
            <Chip label="Polling System" />
            <Chip label="Smoke Check" />
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
}
