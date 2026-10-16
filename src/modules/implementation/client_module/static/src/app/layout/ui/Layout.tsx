import { useState, type ReactNode } from 'react';
import { Box, Drawer, Typography, IconButton } from '@mui/material';
import { Link } from 'react-router-dom';
import { observer } from 'mobx-react-lite';
import { connectionStore } from '@entities/connection';
import { uiStore } from '@entities/ui-settings';
import { DARK, LIGHT } from '@shared/config/theme';
import { Sidebar } from './Sidebar';

const DRAWER_WIDTH = 220;

const ICONS = {
  viewers: { dark: '/images/viewers_b.png', light: '/images/viewers_l.png' },
  computers: { dark: '/images/computers_b.png', light: '/images/computers_l.png' },
  robots: { dark: '/images/robots_b.png', light: '/images/robots_l.png' },
  style: { dark: '/images/style_b.png', light: '/images/style_l.png' },
} as const;

type LayoutProps = { children: ReactNode };

const LayoutInner = ({ children }: LayoutProps) => {
  const isDark = uiStore.themeMode === 'dark';
  const iconTheme = 'dark'; // иконки хедера всегда как в тёмной теме
  const [rotation, setRotation] = useState(0);
  const [glitchKey, setGlitchKey] = useState(0);

  const handleThemeToggle = () => {
    uiStore.toggleTheme();
    setRotation((r) => r + 360);
    setGlitchKey((k) => k + 1);
  };

  const viewers = connectionStore.stats?.viewers ?? 0;
  const pcClients = connectionStore.stats?.pc_clients ?? 0;
  const robots = connectionStore.stats?.robots ?? connectionStore.clientCount;

  return (
    <Box sx={{ display: 'flex', height: '100%', minHeight: 0, bgcolor: 'background.default', p: 1.5, overflow: 'hidden' }}>
      <Drawer
        variant="permanent"
        sx={{
          width: DRAWER_WIDTH,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            top: 12,
            left: 12,
            marginRight: 1.5,
            height: 'calc(100vh - 24px)',
            width: DRAWER_WIDTH,
            boxSizing: 'border-box',
            borderRadius: '10px',
            border: '2px solid',
            borderColor: 'primary.main',
            boxShadow: (t) => (t.palette.mode === 'dark'
              ? '4px 0 24px rgba(96,165,250,0.15), 4px 0 40px rgba(236,72,153,0.08), inset 0 0 0 1px rgba(96,165,250,0.2)'
              : '4px 0 20px rgba(24,120,240,0.2)'),
            bgcolor: isDark ? DARK.sidebarBg : '#ffffff',
            backdropFilter: isDark ? 'blur(16px)' : 'none',
            color: 'secondary.main',
          },
        }}
      >
        <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
          <Sidebar />

          <Typography
            variant="body2"
            sx={{
              flexShrink: 0,
              px: 2,
              pt: 3,
              pb: 2,
              mt: 'auto',
              color: 'secondary.main',
              background: (t) =>
                t.palette.mode === 'dark'
                  ? 'linear-gradient(to bottom, transparent, rgba(96, 165, 250, 0.08))'
                  : 'linear-gradient(to bottom, transparent, rgba(24, 120, 240, 0.04))',
            }}
          >
            {connectionStore.clientCount}
            {connectionStore.clientCount === 1
              ? ' подключение'
              : connectionStore.clientCount >= 2 && connectionStore.clientCount <= 4
                ? ' подключения'
                : ' подключений'}
          </Typography>
        </Box>
      </Drawer>

      <Box
        component="main"
        sx={{
          flex: 1,
          marginLeft: 0,
          width: `calc(100% - ${DRAWER_WIDTH}px)`,
          display: 'flex',
          flexDirection: 'column',
          minWidth: 0,
          minHeight: 0,
          overflow: 'hidden',
        }}
      >
        <Box
          component="header"
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            mt: '2px',
            ml: '25px',
            mr: '25px',
            mb: 0,
            px: 1.5,
            py: 1,
            minHeight: 100,
            height: 100,
            bgcolor: isDark ? DARK.headerBg : LIGHT.headerBg,
            backdropFilter: isDark ? 'blur(16px)' : 'none',
            borderBottom: '2px solid',
            borderColor: 'primary.main',
            boxShadow: 'none',
            flexShrink: 0,
            color: 'secondary.main',
          }}
        >
          <Link to="/" className="artex-logo" style={{ textDecoration: 'none', color: 'inherit' }}>
            <Box sx={{ display: 'flex', flexDirection: 'column', lineHeight: 1.2 }}>
              <Typography
                key={glitchKey}
                sx={{
                  fontFamily: '"Josefin-Bold", sans-serif',
                  fontSize: 38,
                  lineHeight: 'normal',
                  textDecoration: 'none',
                  ...(glitchKey > 0 && { animation: 'artex-glitch 0.45s ease-out' }),
                }}
              >
                ARTEX
              </Typography>

              <Typography
                key={`framework-${glitchKey}`}
                variant="body2"
                sx={{
                  fontFamily: '"Josefin-SemiBold", sans-serif',
                  fontSize: 14,
                  opacity: 0.9,
                  ...(glitchKey > 0 && { animation: 'artex-glitch 0.45s ease-out' }),
                }}
              >
                framework
              </Typography>
            </Box>
          </Link>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0.25 }}>
              <img
                src={ICONS.viewers[iconTheme]}
                alt=""
                width={30}
                height={30}
                style={{
                  filter: isDark ? 'none' : 'invert(92%) sepia(98%) saturate(2000%) hue-rotate(205deg)',
                }}
              />
              <Typography variant="body2" sx={{ fontSize: 22, lineHeight: 1 }}>
                {viewers}
              </Typography>
            </Box>

            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0.25 }}>
              <img
                src={ICONS.computers[iconTheme]}
                alt=""
                width={30}
                height={30}
                style={{
                  filter: isDark ? 'none' : 'invert(92%) sepia(98%) saturate(2000%) hue-rotate(205deg)',
                }}
              />
              <Typography variant="body2" sx={{ fontSize: 22, lineHeight: 1 }}>
                {pcClients}
              </Typography>
            </Box>

            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0.25 }}>
              <img
                src={ICONS.robots[iconTheme]}
                alt=""
                width={30}
                height={30}
                style={{
                  filter: isDark ? 'none' : 'invert(92%) sepia(98%) saturate(2000%) hue-rotate(205deg)',
                }}
              />
              <Typography variant="body2" sx={{ fontSize: 22, lineHeight: 1 }}>
                {robots}
              </Typography>
            </Box>

            <IconButton
              onClick={handleThemeToggle}
              aria-label="тема"
              sx={{
                p: 0,
                alignSelf: 'flex-start',
                bgcolor: 'transparent',
                '&:hover': { bgcolor: 'transparent' },
                '&:focus': { bgcolor: 'transparent' },
                '&.Mui-focusVisible': { bgcolor: 'transparent' },
              }}
              disableRipple
            >
              <img
                src={ICONS.style[iconTheme]}
                alt="Сменить тему"
                width={45}
                height={45}
                style={{
                  transition: 'transform 0.9s cubic-bezier(0.68, -0.55, 0.265, 1.55)',
                  transform: `rotate(${rotation}deg)`,
                  filter: isDark ? 'none' : 'invert(92%) sepia(98%) saturate(2000%) hue-rotate(205deg)',
                }}
              />
            </IconButton>
          </Box>
        </Box>

        <Box sx={{ flex: 1, p: 3, pb: 0, minWidth: 0, width: '100%', display: 'flex', flexDirection: 'column', minHeight: 0, overflow: 'auto' }}>{children}</Box>
      </Box>
    </Box>
  );
};

export const Layout = observer(LayoutInner);
