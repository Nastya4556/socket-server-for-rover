import { useNavigate, useParams } from 'react-router-dom';
import { Box, List, ListItemButton, ListItemText } from '@mui/material';
import { observer } from 'mobx-react-lite';
import { connectionStore } from '@entities/connection';
import { uiStore } from '@entities/ui-settings';
import { subscribe, unsubscribe, sendCommand } from '@features/socket';

const SidebarInner = () => {
  const navigate = useNavigate();
  const { ip } = useParams<{ ip: string }>();
  const robots = connectionStore.robots;
  const ips = Object.keys(robots);
  const isDark = uiStore.themeMode === 'dark';

  const handleSelect = (clientIp: string) => {
    if (connectionStore.currentClientIp) {
      unsubscribe(connectionStore.currentClientIp);
    }
    connectionStore.setCurrentClient(clientIp);
    subscribe(clientIp);
    sendCommand(clientIp, 'pass');
    navigate(`/client/${clientIp}`);
  };

  const handleOverview = () => {
    if (connectionStore.currentClientIp) {
      unsubscribe(connectionStore.currentClientIp);
    }
    connectionStore.setCurrentClient(null);
    connectionStore.setTelem({});
    connectionStore.clearVideo();
    navigate('/');
  };

  const listItemSx = isDark
    ? {
        position: 'relative' as const,
        py: 1,
        minWidth: 0,
        overflow: 'hidden',
        borderRadius: 0,
        borderLeft: '3px solid transparent',
        transition: 'all 0.2s ease',
        '&::before': {
          content: '""',
          position: 'absolute',
          left: 0,
          top: 0,
          bottom: 0,
          width: 0,
          background: 'rgba(96, 165, 250, 0.25)',
          transition: 'width 0.2s ease',
        },
        '&:hover::before': {
          width: '100%',
        },
        '&:hover': {
          borderLeftColor: 'rgba(96, 165, 250, 0.6)',
          backgroundColor: 'transparent',
        },
        '&.Mui-selected': {
          borderLeftColor: '#60a5fa',
          backgroundColor: 'rgba(96, 165, 250, 0.12)',
          '&::before': { width: 0 },
          '&:hover': {
            backgroundColor: 'rgba(96, 165, 250, 0.2)',
          },
        },
        '&.Mui-selected:hover::before': { width: '100%' },
      }
    : {
        position: 'relative' as const,
        py: 1,
        minWidth: 0,
        overflow: 'hidden',
        borderRadius: 0,
        borderLeft: '3px solid transparent',
        transition: 'all 0.2s ease',
        '&::before': {
          content: '""',
          position: 'absolute',
          left: 0,
          top: 0,
          bottom: 0,
          width: 0,
          background: 'rgba(24, 120, 240, 0.25)',
          transition: 'width 0.2s ease',
        },
        '&:hover::before': {
          width: '100%',
        },
        '&:hover': {
          borderLeftColor: 'rgba(24, 120, 240, 0.6)',
          backgroundColor: 'transparent',
        },
        '&.Mui-selected': {
          borderLeftColor: '#1878f0',
          backgroundColor: 'rgba(24, 120, 240, 0.12)',
          color: '#1878f0',
          '&::before': { width: 0 },
          '&:hover': {
            backgroundColor: 'rgba(24, 120, 240, 0.2)',
          },
        },
        '&.Mui-selected:hover::before': { width: '100%' },
      };

  return (
    <Box sx={{ width: '100%', display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 }}>
      <Box
        component="button"
        type="button"
        onClick={handleOverview}
        sx={{
          height: 57,
          minHeight: 57,
          flexShrink: 0,
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          border: 'none',
          backgroundColor: isDark ? '#0000003d' : '#58a9dd30',
          cursor: 'pointer',
          fontFamily: '"Josefin-Bold", sans-serif',
          fontSize: 24,
          color: 'inherit',
          borderBottom: isDark ? '2px solid rgba(96, 165, 250, 0.3)' : (t) => `2px solid ${t.palette.divider}`,
          transition: 'background-color 0.2s ease',
          '&:hover': {
            backgroundColor: isDark ? 'rgba(96, 165, 250, 0.15)' : '#58a9dd30',
          },
        }}
      >
        Подключения
      </Box>

      <List dense sx={{ width: '100%', flex: 1, minHeight: 0, overflow: 'auto' }}>
        {ips.map((clientIp) => {
          const robot = robots[clientIp];
          const isActive = ip === clientIp;
          return (
            <ListItemButton
              key={clientIp}
              selected={isActive}
              onClick={() => handleSelect(clientIp)}
              sx={listItemSx}
            >
              <ListItemText
                primary={robot?.name ?? 'Unknown'}
                secondary={robot?.type ?? ''}
                primaryTypographyProps={{
                  fontFamily: 'monospace',
                  fontSize: '0.9rem',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
                secondaryTypographyProps={{
                  fontSize: '0.75rem',
                  color: 'text.secondary',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
                sx={{ minWidth: 0 }}
              />
            </ListItemButton>
          );
        })}
      </List>
    </Box>
  );
};

export const Sidebar = observer(SidebarInner);
