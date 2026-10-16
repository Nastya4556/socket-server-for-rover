import { useCallback, useEffect } from 'react';
import { Box, Typography, Paper } from '@mui/material';
import { observer } from 'mobx-react-lite';
import { connectionStore } from '@entities/connection';
import { uiStore } from '@entities/ui-settings';
import { sendCommand } from '@features/socket';

const DragOverlayInner = () => {
  const visible = uiStore.dragOverlayVisible;
  const ip = connectionStore.currentClientIp;

  useEffect(() => {
    const handleDragOver = (e: DragEvent) => {
      e.preventDefault();
      if (connectionStore.currentClientIp) uiStore.setDragOverlayVisible(true);
    };
    const handleDragLeave = (e: DragEvent) => {
      if (e.clientX <= 0 || e.clientY <= 0 || e.clientX >= window.innerWidth || e.clientY >= window.innerHeight) {
        uiStore.setDragOverlayVisible(false);
      }
    };
    const handleDrop = (e: DragEvent) => {
      e.preventDefault();
      uiStore.setDragOverlayVisible(false);
      const cip = connectionStore.currentClientIp;
      if (!cip || !e.dataTransfer?.files?.length) return;
      const file = e.dataTransfer.files[0];
      if (!file.name.toLowerCase().endsWith('.py')) return;
      const reader = new FileReader();
      reader.onload = () => {
        sendCommand(cip, 'uploadFile', reader.result as string);
      };
      reader.readAsText(file);
    };
    document.addEventListener('dragover', handleDragOver);
    document.addEventListener('dragleave', handleDragLeave);
    document.addEventListener('drop', handleDrop);
    return () => {
      document.removeEventListener('dragover', handleDragOver);
      document.removeEventListener('dragleave', handleDragLeave);
      document.removeEventListener('drop', handleDrop);
    };
  }, []);

  const handleDropLocal = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      uiStore.setDragOverlayVisible(false);
      if (!ip || !e.dataTransfer.files.length) return;
      const file = e.dataTransfer.files[0];
      if (!file.name.toLowerCase().endsWith('.py')) return;
      const reader = new FileReader();
      reader.onload = () => {
        sendCommand(ip, 'uploadFile', reader.result as string);
      };
      reader.readAsText(file);
    },
    [ip]
  );

  if (!visible) return null;

  return (
    <Box
      onDrop={handleDropLocal}
      onDragOver={(e) => e.preventDefault()}
      sx={{
        position: 'fixed',
        inset: 0,
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        bgcolor: 'rgba(0,0,0,0.5)',
      }}
    >
      <Paper sx={{ p: 4, textAlign: 'center', maxWidth: 320 }}>
        <Typography variant="h6">Перетащите .py файл</Typography>
        <Typography variant="body2" color="text.secondary">
          для загрузки на {ip}
        </Typography>
      </Paper>
    </Box>
  );
};

export const DragOverlay = observer(DragOverlayInner);
