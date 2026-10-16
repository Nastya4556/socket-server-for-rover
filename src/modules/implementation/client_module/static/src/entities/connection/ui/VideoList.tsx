import { useState, useEffect, useRef } from 'react';
import { Box, Typography, useTheme, IconButton } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import { observer } from 'mobx-react-lite';
import { connectionStore } from '../model/connection.store';

const MIN_TILE_SIZE = 120;
const GAP = 8;

const VideoListInner = () => {
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';
  const videoFrames = connectionStore.videoFrames;
  const camIds = Object.keys(videoFrames);
  const [selectedCamId, setSelectedCamId] = useState<string | null>(null);
  const [tileSize, setTileSize] = useState<number>(MIN_TILE_SIZE);
  const containerRef = useRef<HTMLDivElement>(null);

  const displayItems = camIds.map((id) => ({ id, frameSrc: videoFrames[id] }));
  const currentClientIp = connectionStore.currentClientIp;

  useEffect(() => {
    requestAnimationFrame(() => setSelectedCamId(null));
  }, [currentClientIp]);

  // для показа множества камер
  // const displayItems = [
  //   { id: 'Cam 1', frameSrc: videoFrames[camIds[0]] || '' },
  //   { id: 'Cam 2', frameSrc: videoFrames[camIds[0]] || '' },
  //   { id: 'Cam 3', frameSrc: videoFrames[camIds[0]] || '' },
  //   { id: 'Cam 4', frameSrc: videoFrames[camIds[0]] || '' },
  // ];

  const displayCamId = selectedCamId ?? displayItems[0]?.id ?? null;
  const displayFrameSrc = displayItems.find((item) => item.id === displayCamId)?.frameSrc;

  const count = displayItems.length;
  // console.log('item.frameSrc', displayItems, displayItems[0]?.frameSrc, videoFrames);

  useEffect(() => {
    if (count === 1 && displayItems[0]) {
      // setSelectedCamId(displayItems[0].id);
      requestAnimationFrame(() => setSelectedCamId(displayItems[0].id));
    } else if (count > 1 && selectedCamId && !displayItems.find(item => item.id === selectedCamId)) {
      //setSelectedCamId(null);
      requestAnimationFrame(() => setSelectedCamId(null));
    }
  }, [count, displayItems.length]);

  useEffect(() => {
    const el = containerRef.current;
    if (!el || count === 0 || count === 1) return;

    const calculateTileSize = () => {
      const containerWidth = el.clientWidth;
      const containerHeight = el.clientHeight;

      if (containerWidth <= 0 || containerHeight <= 0) return;

      let bestSize = MIN_TILE_SIZE;
      let bestWaste = Infinity;

      const maxPossibleCols = Math.floor((containerWidth + GAP) / (MIN_TILE_SIZE + GAP));

      for (let cols = 1; cols <= Math.min(maxPossibleCols, count); cols++) {
        const rows = Math.ceil(count / cols);

        const availableWidthPerTile = (containerWidth - (cols - 1) * GAP) / cols;
        const availableHeightPerTile = (containerHeight - (rows - 1) * GAP) / rows;

        const candidateSize = Math.min(availableWidthPerTile, availableHeightPerTile);

        if (candidateSize >= MIN_TILE_SIZE) {
          const usedWidth = cols * candidateSize + (cols - 1) * GAP;
          const usedHeight = rows * candidateSize + (rows - 1) * GAP;
          const waste = (containerWidth - usedWidth) + (containerHeight - usedHeight);

          if (candidateSize > bestSize || (candidateSize === bestSize && waste < bestWaste)) {
            bestSize = candidateSize;
            bestWaste = waste;
          }
        }
      }

      const finalSize = Math.floor(bestSize);
      setTileSize(finalSize);
    };

    calculateTileSize();

    const resizeObserver = new ResizeObserver(calculateTileSize);
    resizeObserver.observe(el);

    window.addEventListener('resize', calculateTileSize);

    return () => {
      resizeObserver.disconnect();
      window.removeEventListener('resize', calculateTileSize);
    };
  }, [count]);

  const tileSx = {
    width: tileSize,
    height: tileSize,
    flexShrink: 0,
    display: 'flex',
    flexDirection: 'column',
    border: '1px solid',
    borderColor: 'divider',
    borderRadius: 1,
    overflow: 'hidden',
    cursor: 'pointer',
    boxShadow: isDark ? '0 2px 10px rgba(96,165,250,0.12)' : '0 2px 10px rgba(24,120,240,0.15)',
    '&:hover': { borderColor: 'primary.main' },
  };

  return (
    <Box
      ref={containerRef}
      sx={{
        position: 'relative',
        display: 'flex',
        flexDirection: 'column',
        gap: 2,
        height: '100%',
        minHeight: 0,
        overflow: 'hidden'
      }}
    >
      {displayItems.length > 0 && !selectedCamId && (
        <Box
          sx={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: `${GAP}px`,
            width: '100%',
            height: '100%',
            overflow: 'hidden',
            alignContent: 'flex-start',
          }}
        >
          {displayItems.map((item) => (
            <Box
              key={item.id}
              role="button"
              tabIndex={0}
              onClick={() => setSelectedCamId(item.id)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  setSelectedCamId(item.id);
                }
              }}
              sx={tileSx}
            >
              <Box
                sx={{
                  flexShrink: 0,
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  px: 1,
                  py: 0.25,
                  bgcolor: isDark ? 'background.default' : '#58a9dd30',
                  color: isDark ? '#fff' : 'text.primary',
                }}
              >
                <Typography variant="caption" sx={{ color: 'inherit', fontSize: '0.7rem' }}>
                  {item.id}
                </Typography>
              </Box>
              <Box sx={{ flex: 1, minHeight: 0, overflow: 'hidden' }}>
                <img
                  src={item.frameSrc}
                  alt={`Video ${item.id}`}
                  style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
                />
              </Box>
            </Box>
          ))}
        </Box>
      )}

      {selectedCamId && (
        <Box
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            zIndex: 10,
            display: 'flex',
            flexDirection: 'column',
            bgcolor: 'background.default',
            border: '1px solid',
            borderColor: 'divider',
            borderRadius: 1,
            overflow: 'hidden',
            boxShadow: (t) => (t.palette.mode === 'dark' ? '0 2px 10px rgba(96,165,250,0.12)' : '0 2px 10px rgba(24,120,240,0.15)'),
          }}
        >
          <Box
            sx={{
              flexShrink: 0,
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              px: 1,
              py: 0.5,
              bgcolor: isDark ? 'background.default' : '#58a9dd30',
              color: isDark ? '#fff' : 'text.primary',
            }}
          >
            <Typography variant="caption" sx={{ color: 'inherit' }}>
              Камера: {displayCamId}
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="caption" sx={{ color: 'inherit' }}>
                {new Date().toLocaleTimeString()}
              </Typography>
              {count > 1 && (
                <IconButton
                  size="small"
                  onClick={() => setSelectedCamId(null)}
                  sx={{ color: 'inherit', p: 0.25 }}
                  aria-label="Закрыть"
                >
                  <CloseIcon fontSize="small" />
                </IconButton>
              )}
            </Box>
          </Box>

          <Box sx={{ flex: 1, minHeight: 0, overflow: 'hidden' }}>
            {displayFrameSrc && (
              <img
                src={displayFrameSrc}
                alt={`Video ${displayCamId}`}
                style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
              />
            )}
          </Box>
        </Box>
      )}
    </Box>
  );
};

export const VideoList = observer(VideoListInner);
