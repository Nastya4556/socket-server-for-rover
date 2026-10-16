import { io, type Socket } from 'socket.io-client';
import type { OverviewPayload, TelemPayload, VideoPayload } from '@entities/connection';
import { connectionStore } from '@entities/connection';

const NS = '/client';

const getServerUrl = (): string => {
  if (import.meta.env.VITE_API_ORIGIN) {
    return import.meta.env.VITE_API_ORIGIN;
  }
  return window.location.origin;
};

let socket: Socket | null = null;

const getAuth = (cb: (auth: { name: string; type: string }) => void) => {
  cb({ name: 'TODO browser', type: 'web' });
};

export const initSocket = (): Socket => {
  if (socket?.connected) return socket;

  const serverUrl = getServerUrl();
  
  socket = io(serverUrl + NS, {
    transports: ['websocket'],
    auth: (cb) => getAuth(cb),
  });

  socket.on('connect', () => {
    connectionStore.setConnected(true);
    connectionStore.setSocketId(socket?.id ?? null);
    socket?.emit('connections_ask', null, () => {});
  });

  socket.on('disconnect', () => {
    connectionStore.setConnected(false);
    connectionStore.setSocketId(null);
  });

  socket.on('connect_error', (err) => {
    console.error('Socket connect error:', err.message);
  });

  socket.on('overview', (data: { payload: OverviewPayload }) => {
    connectionStore.setOverview(data.payload);
  });

  socket.on('telem', (data: { payload: TelemPayload }) => {
    connectionStore.setTelem(data.payload);
  });

  socket.on('video', (data: { payload: { payload: VideoPayload } }) => {
    connectionStore.setVideoFrames(data.payload.payload);
  });

  socket.on('token_ask', (_data: unknown, cb: (sid: string) => void) => {
    cb(connectionStore.socketId ?? '');
  });

  socket.on('heartbeat', (data: string[], cb: (ans: Record<string, unknown>) => void) => {
    const ans: Record<string, unknown> = {};
    for (const key of data) {
      if (key === 'd_meta') {
        ans[key] = { sid: connectionStore.socketId, ready: 'ok' };
      } else if (key === 'Ready') {
        ans[key] = 'ok';
      }
    }
    cb(ans);
  });

  socket.on('file', (data: { payload: { type: string; content: string } }) => {
    const { type, content } = data.payload;
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = type + '.txt';
    a.click();
    URL.revokeObjectURL(url);
  });

  return socket;
};

export const getSocket = (): Socket | null => socket;

export const subscribe = (robotId: string) => {
  socket?.emit('subscribe_ask', [robotId], () => {});
};

export const unsubscribe = (robotId: string) => {
  socket?.emit('unsubscribe_ask', [robotId], () => {});
};

export const sendCommand = (
  robotId: string,
  command: string | Record<string, unknown>,
  args?: unknown
) => {
  const payload: Record<string, unknown> = { to_sid: robotId, com: command };
  if (args !== undefined) payload.args = args;
  socket?.emit('command', payload);
};

export const sendFileCommand = (robotId: string, file: string) => {
  socket?.emit('command', { to_sid: robotId, file });
};
