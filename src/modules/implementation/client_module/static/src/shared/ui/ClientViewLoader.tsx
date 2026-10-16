import { Box, Card, Skeleton } from '@mui/material';

export const ClientViewLoader = () => (
  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, flex: 1, minHeight: 0 }}>
    <Card sx={{ p: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexShrink: 0 }}>
      <Skeleton variant="text" width={200} height={32} />
      <Skeleton variant="rounded" width={140} height={36} />
    </Card>

    <Box sx={{ display: 'flex', gap: 1.5, width: '100%', flex: 1, minHeight: 0 }}>
      <Box sx={{ width: '100%', maxWidth: 450, flexShrink: 0, display: 'flex', flexDirection: 'column', gap: 1.5 }}>
        <Card sx={{ p: 2 }}>
          <Skeleton variant="text" width="60%" height={24} sx={{ mb: 1 }} />
          <Skeleton variant="rounded" height={80} sx={{ mb: 1 }} />
          <Skeleton variant="rounded" height={80} />
        </Card>
        <Card sx={{ p: 2, flex: 1 }}>
          <Skeleton variant="text" width={120} height={28} sx={{ mb: 1.5 }} />
          <Skeleton variant="rounded" height={120} />
        </Card>
      </Box>

      <Box sx={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', gap: 1.5 }}>
        <Card sx={{ p: 2, flex: 1 }}>
          <Skeleton variant="text" width={80} height={28} sx={{ mb: 1.5 }} />
          <Skeleton variant="rounded" sx={{ flex: 1, minHeight: 200 }} />
        </Card>
      </Box>
    </Box>
  </Box>
);
