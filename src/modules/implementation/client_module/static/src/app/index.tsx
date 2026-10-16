import { useEffect, useLayoutEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider, CssBaseline } from '@mui/material';
import { observer } from 'mobx-react-lite';

import { queryClient, getAppTheme } from '@shared';
import { uiStore } from '@entities/ui-settings';
import { initSocket } from '@features/socket';
import { Layout } from './layout';
import { DragOverlay } from '@widgets/drag-overlay';
import { ClientViewPage } from '@pages/client-view';
import { OverviewPage } from '@pages/overview';

const AppContent = observer(() => {
  const isDark = uiStore.themeMode === 'dark';
  const theme = getAppTheme(isDark ? 'dark' : 'light');

  useLayoutEffect(() => {
    document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
  }, [isDark]);

  useEffect(() => {
    initSocket();
  }, []);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<OverviewPage />} />
            <Route path="/client/:ip" element={<ClientViewPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Layout>
        <DragOverlay />
      </BrowserRouter>
    </ThemeProvider>
  );
});

const App = () => (
  <QueryClientProvider client={queryClient}>
    <AppContent />
  </QueryClientProvider>
);

export default App;
