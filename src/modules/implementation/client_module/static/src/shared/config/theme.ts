import { createTheme, type PaletteMode } from '@mui/material/styles';

/** Киберпанк тёмная — electric blue + neon magenta */
export const DARK = {
  mainBg: '#080810',
  sidebarBg: 'rgba(15, 15, 28, 0.85)',
  headerBg: 'rgba(18, 18, 35, 0.9)',
  cardBg: 'rgba(20, 25, 45, 0.5)',
  cardBgAlt: 'rgba(45, 25, 55, 0.45)',
  accent: '#60a5fa',
  accentSecondary: '#ec4899',
  border: 'rgba(96, 165, 250, 0.35)',
  borderGlow: 'rgba(96, 165, 250, 0.15)',
  textOnDark: '#e0e7ff',
  textSecondary: '#a5b4fc',
} as const;

/** Светлая тема — стиль React docs: белый, синий акцент */
export const LIGHT = {
  mainBg: '#fcfcfc',
  sidebarBg: '#ffffff',
  headerBg: '#ffffff',
  cardBg: '#f6f8fa',
  cardBgAlt: '#e8f0f7',
  accent: '#1878f0',
  accentSecondary: '#0d6efd',
  border: 'rgba(24, 120, 240, 0.25)',
  borderGlow: 'rgba(24, 120, 240, 0.08)',
  textOnDark: '#c4b5fd',
  textOnLight: '#20232a',
  textOnLightMuted: '#757575',
} as const;

export const getAppTheme = (mode: PaletteMode) => {
  const isDark = mode === 'dark';
  const c = isDark ? DARK : LIGHT;
  return createTheme({
    palette: {
      mode,
      primary: { main: c.accent },
      secondary: { main: isDark ? c.textOnDark : LIGHT.textOnLight },
      background: {
        default: c.mainBg,
        paper: c.sidebarBg,
      },
      text: {
        primary: isDark ? c.textOnDark : LIGHT.textOnLight,
        secondary: isDark ? c.textOnDark : LIGHT.textOnLightMuted,
      },
      divider: c.border,
    },
    typography: {
      fontFamily: '"Kanit", "Josefin-Bold", "Josefin-SemiBold", sans-serif',
      h6: { fontWeight: 600 },
    },
    shape: { borderRadius: 8 },
    components: {
      MuiButton: {
        styleOverrides: {
          root: {
            textTransform: 'none',
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: ({ theme }) => {
            const isDark = theme.palette.mode === 'dark';
            const glow = isDark
              ? '0 0 20px rgba(96,165,250,0.1), 0 0 30px rgba(236,72,153,0.05)'
              : '0 4px 16px rgba(24,120,240,0.18)';
            return {
              background: isDark ? DARK.cardBg : LIGHT.cardBg,
              backdropFilter: 'blur(12px)',
              border: `1px solid ${theme.palette.divider}`,
              boxShadow: glow,
              ...(theme.palette.mode === 'light' && { color: theme.palette.text.primary }),
            };
          },
        },
      },
      MuiPaper: {
        styleOverrides: {
          root: ({ theme }) => {
            const isDark = theme.palette.mode === 'dark';
            const glow = isDark
              ? '0 0 12px rgba(96,165,250,0.06), 0 0 20px rgba(236,72,153,0.03)'
              : '0 2px 12px rgba(24,120,240,0.15)';
            return {
              background: isDark ? 'rgba(15, 20, 40, 0.35)' : '#f6f8fa',
              backdropFilter: isDark ? 'blur(8px)' : 'none',
              border: `1px solid ${theme.palette.divider}`,
              boxShadow: glow,
            };
          },
        },
      },
    },
  });
};
