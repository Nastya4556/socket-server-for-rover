import { makeAutoObservable } from 'mobx';
import type { OverviewPayload, RobotData, TelemPayload, VideoPayload } from './types';

export class ConnectionStore {
  /** Текущий выбранный IP клиента (null = сводка) */
  currentClientIp: string | null = null;

  /** Данные overview с сервера */
  robots: Record<string, RobotData> = {};
  stats: OverviewPayload['stats'] = {};

  /** Телеметрия выбранного клиента */
  telem: TelemPayload = {};

  /** Видеопотоки выбранного клиента: camId -> url или null */
  videoFrames: Record<string, string> = {};

  /** Socket ID текущего браузера */
  socketId: string | null = null;

  /** Подключён ли сокет */
  connected = false;

  /** Время последней смены клиента — игнорировать video N мс после смены (race с late-кадром от старого робота) */
  videoSwitchAt = 0;

  constructor() {
    makeAutoObservable(this);
  }

  setOverview(payload: OverviewPayload) {
    this.robots = payload.robots ?? {};
    this.stats = payload.stats ?? {};
  }

  setCurrentClient(ip: string | null) {
    this.currentClientIp = ip;
    if (!ip) {
      this.telem = {};
      this.videoFrames = {};
    }
  }

  setTelem(payload: TelemPayload) {
    this.telem = { ...payload };
  }

  markVideoSwitch() {
    this.videoSwitchAt = Date.now();
  }

  setVideoFrames(data: VideoPayload) {
    if (Date.now() - this.videoSwitchAt < 80) return;
    const next: Record<string, string> = {};
    for (const camId of Object.keys(this.videoFrames)) {
      if (!(camId in data)) URL.revokeObjectURL(this.videoFrames[camId]);
    }
    for (const [camId, frameData] of Object.entries(data)) {
      try {
        let blob: Blob;
        if (typeof frameData === 'string') {
          // Socket.IO может передать байты как base64
          const bin = Uint8Array.from(atob(frameData), (c) => c.charCodeAt(0));
          blob = new Blob([bin], { type: 'image/jpeg' });
        } else {
          blob = new Blob([frameData as BlobPart], { type: 'image/jpeg' });
        }
        const url = URL.createObjectURL(blob);
        if (this.videoFrames[camId]) URL.revokeObjectURL(this.videoFrames[camId]);
        next[camId] = url;
      } catch (e) {
        console.error('[video] frame error', camId, e);
      }
    }
    this.videoFrames = next;
  }

  clearVideo() {
    Object.values(this.videoFrames).forEach((url) => URL.revokeObjectURL(url));
    this.videoFrames = {};
  }

  setSocketId(id: string | null) {
    this.socketId = id;
  }

  setConnected(value: boolean) {
    this.connected = value;
  }

  get currentRobot(): RobotData | null {
    if (!this.currentClientIp) return null;
    return this.robots[this.currentClientIp] ?? null;
  }

  get clientCount(): number {
    return Object.keys(this.robots).length;
  }
}

export const connectionStore = new ConnectionStore();
