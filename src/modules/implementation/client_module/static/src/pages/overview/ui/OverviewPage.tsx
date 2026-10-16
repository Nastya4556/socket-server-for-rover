import { Box, Card, Typography, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper } from '@mui/material';
import { observer } from 'mobx-react-lite';
import { connectionStore } from '@entities/connection';

export const OverviewPage = observer(() => {
  const robots = connectionStore.robots ?? {};

  const typeCounts = Object.values(robots).reduce<Record<string, number>>((acc, r) => {
    const t = r.type ?? 'unknown';
    acc[t] = (acc[t] ?? 0) + 1;
    return acc;
  }, {});

  const ips = Object.keys(robots);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, width: '100%', maxWidth: '100%' }}>
      <Card
        sx={{
          p: 2,
          width: '100%',
          border: '2px solid',
          borderColor: 'primary.main',
        }}
      >
        <Typography variant="h6" gutterBottom color="text.primary">
          Сводка подключений
        </Typography>

        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
          {Object.entries(typeCounts).map(([type, count]) => {
            const isUnknown = type === 'unknown';
            return (
              <Box
                key={type}
                sx={{
                  p: 2,
                  minWidth: 120,
                  borderRadius: 1,
                  bgcolor: (t) => {
                    if (t.palette.mode === 'dark') {
                      return isUnknown ? 'rgba(25, 35, 55, 0.5)' : 'rgba(20, 35, 60, 0.5)';
                    }
                    return isUnknown ? '#eef2f8' : '#e8f0f7';
                  },
                  border: '1px solid',
                  borderColor: isUnknown ? 'divider' : 'primary.main',
                  boxShadow: (t) => (t.palette.mode === 'dark'
                    ? '0 2px 8px rgba(96,165,250,0.15)'
                    : isUnknown
                      ? '0 2px 8px rgba(24,120,240,0.15)'
                      : '0 2px 10px rgba(24,120,240,0.2)'),
                }}
              >
                <Typography
                  variant="body2"
                  sx={{
                    color: isUnknown
                      ? (t) => (t.palette.mode === 'dark' ? '#94a3b8' : '#757575')
                      : 'secondary.main',
                  }}
                >
                  {type}
                </Typography>
                <Typography
                  variant="h6"
                  sx={{
                    color: isUnknown
                      ? (t) => (t.palette.mode === 'dark' ? '#94a3b8' : '#757575')
                      : 'secondary.main',
                  }}
                >
                  {count}
                </Typography>
              </Box>
            );
          })}
        </Box>
      </Card>

      <Card
        sx={{
          p: 2,
          pb: '50px',
          width: '100%',
          border: '2px solid',
          borderColor: 'primary.main',
        }}
      >
        <Typography variant="h6" gutterBottom color="text.primary">
          Таблица подключений
        </Typography>
        <TableContainer
          component={Paper}
          variant="outlined"
          sx={{
            width: '100%',
            overflowX: 'auto',
            bgcolor: (t) => t.palette.mode === 'dark' ? 'rgba(15, 20, 40, 0.4)' : '#f6f8fa',
            backdropFilter: 'blur(8px)',
            boxShadow: (t) => (t.palette.mode === 'dark'
              ? '0 2px 12px rgba(96,165,250,0.12)'
              : '0 2px 12px rgba(24,120,240,0.15)'),
          }}
        >
          <Table size="small" sx={{ width: '100%', tableLayout: 'auto' }}>
            <TableHead>
              <TableRow>
                <TableCell sx={{ width: 48 }}>#</TableCell>
                <TableCell sx={{ fontFamily: 'monospace' }}>SID</TableCell>
                <TableCell>Имя</TableCell>
                <TableCell>Тип</TableCell>
                <TableCell>ВТК</TableCell>
                <TableCell>Батарея</TableCell>
              </TableRow>
            </TableHead>

            <TableBody>
              {ips.map((ip, idx) => {
                const robot = robots[ip];
                const telem = robot?.posibilities?.telemetry;
                const video = robot?.posibilities?.video;
                const telemSrc =
                  telem === true
                    ? '/images/true_check.png'
                    : telem === false
                      ? '/images/false_check.png'
                      : '/images/error_check.png';
                const videoSrc =
                  video === true
                    ? '/images/true_check.png'
                    : video === false
                      ? '/images/false_check.png'
                      : '/images/error_check.png';

                return (
                  <TableRow key={ip}>
                    <TableCell>{idx + 1}</TableCell>
                    <TableCell sx={{ fontFamily: 'monospace' }}>{ip}</TableCell>
                    <TableCell>{robot?.name ?? '—'}</TableCell>
                    <TableCell>{robot?.type ?? '—'}</TableCell>
                    <TableCell sx={{ display: 'flex', gap: 0.5, alignItems: 'center' }}>
                      <Box component="img" src={telemSrc} alt="" title="Телеметрия" sx={{ width: 20, height: 20 }} />
                      <Box component="img" src={videoSrc} alt="" title="Видео" sx={{ width: 20, height: 20 }} />
                    </TableCell>
                    <TableCell>{robot?.battery ?? '—'}</TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>
      </Card>
    </Box>
  );
});
