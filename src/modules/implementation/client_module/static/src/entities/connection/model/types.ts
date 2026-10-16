export interface RobotData {
  name: string;
  type: 'Robot' | 'Drone' | 'LED' | string;
  battery?: string;
  posibilities?: {
    telemetry?: boolean;
    video?: boolean;
  };
}

/** Сводка: robots[ip] = RobotData, stats = счётчики */
export interface OverviewPayload {
  robots: Record<string, RobotData>;
  stats?: {
    viewers?: number;
    pc_clients?: number;
    robots?: number;
    [key: string]: number | undefined;
  };
}

/** Телеметрия — произвольный объект ключ-значение */
export interface TelemPayload {
  [key: string]: unknown;
}

/** Видео: camId -> бинарные данные кадра или base64 (при передаче через Socket.IO) */
export interface VideoPayload {
  [camId: string]: ArrayBuffer | Uint8Array | string;
}
