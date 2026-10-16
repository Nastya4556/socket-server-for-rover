import { useState, useEffect, useCallback } from "react";
import { Box, Button, TextField, Typography, useTheme } from "@mui/material";
import { observer } from "mobx-react-lite";

import type { RobotData } from "@entities/connection";
import { uiStore } from "@entities/ui-settings";
import { sendCommand } from "@features/socket";
import { connectionStore } from "@entities/connection";

const ARROWS = {
  dark: {
    arrow: "/images/arrow_b.png",
    turn: "/images/arrow_turn_b.png",
    droneUp: "/images/drone_up_b.png",
    droneDown: "/images/drone_down_b.png",
  },
  light: {
    arrow: "/images/arrow_l.png",
    turn: "/images/arrow_turn_l.png",
    droneUp: "/images/drone_up_l.png",
    droneDown: "/images/drone_down_l.png",
  },
} as const;

type ClientControlProps = { robotId: string; robot: RobotData };

type CmdFn = (c: string | Record<string, unknown>, args?: unknown) => void;

const GridBtn = ({
  onPress,
  onRelease,
  src,
  active = false,
  sx = {},
}: {
  onPress: () => void;
  onRelease: () => void;
  src: string;
  active?: boolean;
  sx?: object;
}) => {
  const [pressed, setPressed] = useState(false);
  const theme = useTheme();
  const isActive = active || pressed;
  const isDark = theme.palette.mode === "dark";
  const glow = isDark ? "96, 165, 250" : "24, 120, 240";
  return (
    <Box
      component="button"
      type="button"
      onMouseDown={(e) => {
        e.preventDefault();
        setPressed(true);
        onPress();
      }}
      onMouseUp={() => {
        setPressed(false);
        onRelease();
      }}
      onMouseLeave={() => {
        if (pressed) {
          setPressed(false);
          onRelease();
        }
      }}
      sx={{
        border: "2px solid",
        borderColor: isActive ? "primary.main" : "divider",
        backgroundColor: isActive ? `rgba(${glow}, 0.25)` : "transparent",
        boxShadow: isActive
          ? `0 0 12px rgba(${glow}, 0.3), inset 0 0 8px rgba(${glow}, 0.15)`
          : "none",
        borderRadius: "12px",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        cursor: "pointer",
        transition: "all 0.2s ease",
        "&:hover": {
          borderColor: "primary.main",
          backgroundColor: `rgba(${glow}, 0.15)`,
          boxShadow: `0 0 8px rgba(${glow}, 0.2)`,
        },
        ...sx,
      }}
    >
      <Box
        component="img"
        src={src}
        alt=""
        sx={{
          width: "80%",
          height: "80%",
          objectFit: "contain",
          pointerEvents: "none",
        }}
      />
    </Box>
  );
};

const RobotControl = observer(
  ({
    cmd,
    activeCommands,
  }: {
    robotId: string;
    cmd: CmdFn;
    activeCommands: Set<string>;
  }) => {
    const [commandInput, setCommandInput] = useState("");
    const theme = uiStore.themeMode === "dark" ? "dark" : "light";
    const { arrow, turn } = ARROWS[theme];

    return (
      <Box
        sx={{
          p: 2,
          border: "1px solid",
          borderColor: "divider",
          borderRadius: 2,
          bgcolor: (t) =>
            t.palette.mode === "light" ? "#58a9dd30" : "transparent",
          boxShadow: (t) =>
            t.palette.mode === "dark"
              ? "0 2px 12px rgba(96,165,250,0.12)"
              : "0 2px 12px rgba(24,120,240,0.15)",
        }}
      >
        <Box component="h3" sx={{ mt: 0, mb: 2 }}>
          Управление клиентом
        </Box>

        <Box
          sx={{
            display: "grid",
            gridTemplateColumns: "repeat(3, 70px)",
            gridTemplateRows: "repeat(3, 70px)",
            gap: 1.25,
            justifyContent: "center",
          }}
        >
          <GridBtn
            onPress={() => cmd("down")}
            onRelease={() => cmd("stop")}
            src={turn}
            active={activeCommands.has("down")}
            sx={{ "& img": { width: "70%", height: "70%" } }}
          />
          <GridBtn
            onPress={() => cmd("forward")}
            onRelease={() => cmd("stop")}
            src={arrow}
            active={activeCommands.has("forward")}
            sx={{ "& img": { transform: "rotate(-90deg)" } }}
          />
          <GridBtn
            onPress={() => cmd("up")}
            onRelease={() => cmd("stop")}
            src={turn}
            active={activeCommands.has("up")}
            sx={{
              "& img": { width: "70%", height: "70%", transform: "scaleX(-1)" },
            }}
          />
          <GridBtn
            onPress={() => cmd("left")}
            onRelease={() => cmd("stop")}
            src={arrow}
            active={activeCommands.has("left")}
            sx={{ "& img": { transform: "rotate(180deg)" } }}
          />
          <Box />
          <GridBtn
            onPress={() => cmd("right")}
            onRelease={() => cmd("stop")}
            src={arrow}
            active={activeCommands.has("right")}
          />
          <Box />
          <GridBtn
            onPress={() => cmd("back")}
            onRelease={() => cmd("stop")}
            src={arrow}
            active={activeCommands.has("back")}
            sx={{ "& img": { transform: "rotate(90deg)" } }}
          />
          <Box />
        </Box>

        <Box sx={{ display: "flex", gap: 1, mt: 2, flexWrap: "wrap" }}>
          <Button variant="contained" color="error" onClick={() => cmd("stop")}>
            Стоп
          </Button>
          <Button variant="outlined" onClick={() => cmd("disarm")}>
            DISARM
          </Button>
        </Box>
        <Box sx={{ display: "flex", gap: 1, mt: 2 }}>
          <TextField
            size="small"
            placeholder="Введите команду..."
            value={commandInput}
            onChange={(e) => setCommandInput(e.target.value)}
            onKeyDown={(e) =>
              e.key === "Enter" && (cmd(commandInput), setCommandInput(""))
            }
            sx={{ flex: 1 }}
          />
          <Button
            variant="contained"
            onClick={() => (cmd(commandInput), setCommandInput(""))}
          >
            Отправить
          </Button>
        </Box>
      </Box>
    );
  },
);

const DroneControl = observer(
  ({
    cmd,
    activeCommands,
  }: {
    robotId: string;
    cmd: CmdFn;
    activeCommands: Set<string>;
  }) => {
    const [commandInput, setCommandInput] = useState("");
    const theme = uiStore.themeMode === "dark" ? "dark" : "light";
    const { arrow, droneUp, droneDown } = ARROWS[theme];

    return (
      <Box
        sx={{
          p: 2,
          border: "1px solid",
          borderColor: "divider",
          borderRadius: 2,
          bgcolor: (t) =>
            t.palette.mode === "light" ? "#58a9dd30" : "transparent",
          boxShadow: (t) =>
            t.palette.mode === "dark"
              ? "0 2px 12px rgba(96,165,250,0.12)"
              : "0 2px 12px rgba(24,120,240,0.15)",
        }}
      >
        <Box component="h3" sx={{ mt: 0, mb: 2 }}>
          Управление клиентом
        </Box>
        <Box sx={{ display: "flex", justifyContent: "center", gap: 2, mb: 2 }}>
          <GridBtn
            onPress={() => cmd("up")}
            onRelease={() => cmd("stop")}
            src={droneUp}
            active={activeCommands.has("up")}
            sx={{ width: 70, height: 70 }}
          />
          <GridBtn
            onPress={() => cmd("down")}
            onRelease={() => cmd("stop")}
            src={droneDown}
            active={activeCommands.has("down")}
            sx={{ width: 70, height: 70 }}
          />
        </Box>
        <Box
          sx={{
            display: "grid",
            gridTemplateColumns: "repeat(3, 70px)",
            gridTemplateRows: "repeat(3, 70px)",
            gap: 1.25,
            justifyContent: "center",
          }}
        >
          <Box />
          <GridBtn
            onPress={() => cmd("forward")}
            onRelease={() => cmd("stop")}
            src={arrow}
            active={activeCommands.has("forward")}
            sx={{ "& img": { transform: "rotate(-90deg)" } }}
          />
          <Box />
          <GridBtn
            onPress={() => cmd("left")}
            onRelease={() => cmd("stop")}
            src={arrow}
            active={activeCommands.has("left")}
            sx={{ "& img": { transform: "rotate(180deg)" } }}
          />
          <Box />
          <GridBtn
            onPress={() => cmd("right")}
            onRelease={() => cmd("stop")}
            src={arrow}
            active={activeCommands.has("right")}
          />
          <Box />
          <GridBtn
            onPress={() => cmd("back")}
            onRelease={() => cmd("stop")}
            src={arrow}
            active={activeCommands.has("back")}
            sx={{ "& img": { transform: "rotate(90deg)" } }}
          />
          <Box />
        </Box>
        <Box sx={{ display: "flex", gap: 1, mt: 2 }}>
          <Button variant="contained" color="error" onClick={() => cmd("stop")}>
            Стоп
          </Button>
          <Button variant="outlined" onClick={() => cmd("disarm")}>
            DISARM
          </Button>
        </Box>
        <Box sx={{ display: "flex", gap: 1, mt: 2 }}>
          <TextField
            size="small"
            placeholder="Команда..."
            value={commandInput}
            onChange={(e) => setCommandInput(e.target.value)}
            onKeyDown={(e) =>
              e.key === "Enter" && (cmd(commandInput), setCommandInput(""))
            }
            sx={{ flex: 1 }}
          />
          <Button
            variant="contained"
            onClick={() => (cmd(commandInput), setCommandInput(""))}
          >
            Отправить
          </Button>
        </Box>
      </Box>
    );
  },
);

/** По code (физическая клавиша), не зависит от раскладки */
const CODE_TO_CMD: Record<string, string> = {
  KeyW: "forward",
  KeyS: "back",
  KeyA: "left",
  KeyD: "right",
  KeyQ: "down",
  KeyE: "up",
};

const ClientControlInner = ({ robotId, robot }: ClientControlProps) => {
  const type = robot?.type ?? "";
  const [activeCommands, setActiveCommands] = useState<Set<string>>(new Set());

  const cmd = useCallback(
    (c: string | Record<string, unknown>, args?: unknown) => {
      sendCommand(robotId, c, args);
    },
    [robotId],
  );

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (["INPUT", "TEXTAREA"].includes((e.target as HTMLElement)?.tagName))
        return;
      const command = CODE_TO_CMD[e.code];

      if (command) {
        setActiveCommands((prev) => {
          if (prev.has(command)) return prev;
          const next = new Set(prev);
          next.add(command);
          cmd(command);
          return next;
        });
        e.preventDefault();
      }
    };

    const handleKeyUp = (e: KeyboardEvent) => {
      const command = CODE_TO_CMD[e.code];
      if (command) {
        setActiveCommands((prev) => {
          if (!prev.has(command)) return prev;
          const next = new Set(prev);
          next.delete(command);
          cmd("stop");
          return next;
        });
        e.preventDefault();
      }
    };

    const handleBlur = () => {
      setActiveCommands((prev) => {
        if (prev.size === 0) return prev;
        cmd("stop");
        return new Set();
      });
    };

    document.addEventListener("keydown", handleKeyDown, true);
    document.addEventListener("keyup", handleKeyUp, true);
    window.addEventListener("blur", handleBlur);
    return () => {
      document.removeEventListener("keydown", handleKeyDown, true);
      document.removeEventListener("keyup", handleKeyUp, true);
      window.removeEventListener("blur", handleBlur);
    };
  }, [cmd]);

  if (type === "Robot") {
    return (
      <RobotControl
        robotId={robotId}
        cmd={cmd}
        activeCommands={activeCommands}
      />
    );
  }

  if (type === "Drone") {
    return (
      <DroneControl
        robotId={robotId}
        cmd={cmd}
        activeCommands={activeCommands}
      />
    );
  }

  if (type === "LED") {
    return <LedControl robotId={robotId} cmd={cmd} />;
  }

  // Временно: fallback на RobotControl для неизвестных типов
  return null;
};

// HEX-палитра: параметры и генерация сетки
const PALETTE_CX = 190;
const PALETTE_CY = 190;
const BIG_RADIUS = 180;
const SMALL_R = 12;

// const hexPoint = (cx: number, cy: number, r: number, i: number) => {
//   const angle = (Math.PI / 3) * i - Math.PI / 6;
//   return { x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle) };
// };

// const createPaletteTiles = () => {
//   const vertices: { x: number; y: number }[] = [];
//   for (let i = 0; i < 6; i++) vertices.push(hexPoint(PALETTE_CX, PALETTE_CY, BIG_RADIUS, i));

//   const anchors = {
//     R: { x: vertices[0].x, y: vertices[0].y, color: [255, 0, 0] as [number, number, number] },
//     Y: { x: vertices[1].x, y: vertices[1].y, color: [255, 255, 0] as [number, number, number] },
//     G: { x: vertices[2].x, y: vertices[2].y, color: [0, 255, 0] as [number, number, number] },
//     C: { x: vertices[3].x, y: vertices[3].y, color: [0, 255, 255] as [number, number, number] },
//     B: { x: vertices[4].x, y: vertices[4].y, color: [0, 0, 255] as [number, number, number] },
//     M: { x: vertices[5].x, y: vertices[5].y, color: [255, 0, 255] as [number, number, number] },
//   };

//   const mixColor = (x: number, y: number): string => {
//     const k = 60;
//     const weights: { w: number; color: [number, number, number] }[] = [];
//     let sum = 0;
//     for (const a of Object.values(anchors)) {
//       const d = Math.sqrt((x - a.x) ** 2 + (y - a.y) ** 2);
//       const w = Math.exp(-d / k);
//       weights.push({ w, color: a.color });
//       sum += w;
//     }
//     let R = 0, G = 0, B = 0;
//     for (const p of weights) {
//       const factor = p.w / sum;
//       R += p.color[0] * factor;
//       G += p.color[1] * factor;
//       B += p.color[2] * factor;
//     }
//     const dCenter = Math.hypot(x - PALETTE_CX, y - PALETTE_CY);
//     const boost = Math.max(0, 1 - dCenter / BIG_RADIUS);
//     const maxC = Math.max(R, G, B);
//     if (maxC > 0) {
//       const scale = 1 + ((255 / maxC) - 1) * boost;
//       R *= scale; G *= scale; B *= scale;
//       R = Math.min(R, 255); G = Math.min(G, 255); B = Math.min(B, 255);
//     }
//     R = Math.max(0, R - 18); G = Math.max(0, G - 18); B = Math.max(0, B - 18);
//     const m = Math.max(R, G, B);
//     R = Math.floor((R * 255) / m);
//     G = Math.floor((G * 255) / m);
//     B = Math.floor((B * 255) / m);
//     return `rgb(${R | 0},${G | 0},${B | 0})`;
//   };

//   const smallHex = (x: number, y: number, r: number) => {
//     const pts: string[] = [];
//     for (let i = 0; i < 6; i++) {
//       const angle = (Math.PI / 3) * i;
//       pts.push(`${x + r * Math.cos(angle)},${y + r * Math.sin(angle)}`);
//     }
//     return pts.join(' ');
//   };

//   const insideBigHex = (x: number, y: number) => {
//     let intersections = 0;
//     for (let i = 0; i < 6; i++) {
//       const j = (i + 1) % 6;
//       const [x1, y1] = [vertices[i].x, vertices[i].y];
//       const [x2, y2] = [vertices[j].x, vertices[j].y];
//       if ((y1 > y) !== (y2 > y) && x < ((x2 - x1) * (y - y1)) / (y2 - y1) + x1) intersections++;
//     }
//     return intersections % 2 === 1;
//   };

//   const h = SMALL_R * Math.sqrt(3);
//   const tiles: { points: string; fill: string }[] = [];
//   for (let row = -30; row <= 30; row++) {
//     for (let col = -30; col <= 30; col++) {
//       const x = PALETTE_CX + col * (SMALL_R * 1.5);
//       const y = PALETTE_CY + row * h + (col % 2 ? h / 2 : 0);
//       if (!insideBigHex(x, y)) continue;
//       tiles.push({ points: smallHex(x, y, SMALL_R), fill: mixColor(x, y) });
//     }
//   }
//   return tiles;
// };

// const PALETTE_TILES = createPaletteTiles();

const hexPoint = (cx: number, cy: number, r: number, i: number) => {
  const angle = (Math.PI / 3) * i - Math.PI / 6;
  return { x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle) };
};

const createPaletteTiles = () => {
  const vertices: { x: number; y: number }[] = [];
  for (let i = 0; i < 6; i++)
    vertices.push(hexPoint(PALETTE_CX, PALETTE_CY, BIG_RADIUS, i));

  const anchors = {
    R: {
      x: vertices[0].x,
      y: vertices[0].y,
      color: [255, 0, 0] as [number, number, number],
    },
    Y: {
      x: vertices[1].x,
      y: vertices[1].y,
      color: [255, 255, 0] as [number, number, number],
    },
    G: {
      x: vertices[2].x,
      y: vertices[2].y,
      color: [0, 255, 0] as [number, number, number],
    },
    C: {
      x: vertices[3].x,
      y: vertices[3].y,
      color: [0, 255, 255] as [number, number, number],
    },
    B: {
      x: vertices[4].x,
      y: vertices[4].y,
      color: [0, 0, 255] as [number, number, number],
    },
    M: {
      x: vertices[5].x,
      y: vertices[5].y,
      color: [255, 0, 255] as [number, number, number],
    },
  };

  // Передаем vertices в функцию insideBigHex
  const insideBigHex = (x: number, y: number): boolean => {
    let intersections = 0;
    for (let i = 0; i < 6; i++) {
      const j = (i + 1) % 6;
      const [x1, y1] = [vertices[i].x, vertices[i].y];
      const [x2, y2] = [vertices[j].x, vertices[j].y];
      if (y1 > y !== y2 > y && x < ((x2 - x1) * (y - y1)) / (y2 - y1) + x1)
        intersections++;
    }
    return intersections % 2 === 1;
  };

  const mixColor = (x: number, y: number): string => {
    // ... весь код mixColor без изменений
    const k = 60;
    const weights: { w: number; color: [number, number, number] }[] = [];
    let sum = 0;
    for (const a of Object.values(anchors)) {
      const d = Math.sqrt((x - a.x) ** 2 + (y - a.y) ** 2);
      const w = Math.exp(-d / k);
      weights.push({ w, color: a.color });
      sum += w;
    }
    let R = 0,
      G = 0,
      B = 0;
    for (const p of weights) {
      const factor = p.w / sum;
      R += p.color[0] * factor;
      G += p.color[1] * factor;
      B += p.color[2] * factor;
    }
    const dCenter = Math.hypot(x - PALETTE_CX, y - PALETTE_CY);
    const boost = Math.max(0, 1 - dCenter / BIG_RADIUS);
    const maxC = Math.max(R, G, B);
    if (maxC > 0) {
      const scale = 1 + (255 / maxC - 1) * boost;
      R *= scale;
      G *= scale;
      B *= scale;
      R = Math.min(R, 255);
      G = Math.min(G, 255);
      B = Math.min(B, 255);
    }
    R = Math.max(0, R - 18);
    G = Math.max(0, G - 18);
    B = Math.max(0, B - 18);
    const m = Math.max(R, G, B);
    R = Math.floor((R * 255) / m);
    G = Math.floor((G * 255) / m);
    B = Math.floor((B * 255) / m);
    return `rgb(${R | 0},${G | 0},${B | 0})`;
  };

  const smallHex = (x: number, y: number, r: number) => {
    const pts: string[] = [];
    for (let i = 0; i < 6; i++) {
      const angle = (Math.PI / 3) * i;
      pts.push(`${x + r * Math.cos(angle)},${y + r * Math.sin(angle)}`);
    }
    return pts.join(" ");
  };

  const h = SMALL_R * Math.sqrt(3);
  const tiles: { points: string; fill: string }[] = [];
  for (let row = -30; row <= 30; row++) {
    for (let col = -30; col <= 30; col++) {
      const x = PALETTE_CX + col * (SMALL_R * 1.5);
      const y = PALETTE_CY + row * h + (col % 2 ? h / 2 : 0);
      if (!insideBigHex(x, y)) continue;
      tiles.push({ points: smallHex(x, y, SMALL_R), fill: mixColor(x, y) });
    }
  }
  return tiles;
};

const PALETTE_TILES = createPaletteTiles();

const LedControl = ({
  cmd,
}: {
  robotId: string;
  cmd: (c: string | Record<string, unknown>, args?: unknown) => void;
}) => {
  const [hex, setHex] = useState("");
  const [currentColor, setCurrentColor] = useState<string | null>(null);
  //const [isDragging, setIsDragging] = useState(false);
  const telem = connectionStore.telem;

  const serverBrightness =
    typeof telem["Brightness"] === "number"
      ? Math.round((telem["Brightness"] as number) * 100)
      : 50;
  // const brightness = isDragging ? dragValue : serverBrightness;

  const [dragValue, setDragValue] = useState(serverBrightness);

  const sendColor = (rgbStr: string) => {
    cmd({ color: rgbStr });
  };

  const handlePaletteClick = useCallback(
    (rgbStr: string) => {
      const result = rgbStr
        .replace("rgb(", "")
        .replace(")", "")
        .replace(/,/g, ".");
      setCurrentColor(rgbStr);
      cmd({ color: result });
    },
    [cmd],
  );

  const handleHexSubmit = () => {
    const h = hex.replace(/^#/, "");
    if (!/^[0-9A-Fa-f]{6}$/.test(h)) return;
    const r = parseInt(h.slice(0, 2), 16);
    const g = parseInt(h.slice(2, 4), 16);
    const b = parseInt(h.slice(4, 6), 16);
    sendColor(`${r}.${g}.${b}`);
  };

  return (
    <Box
      sx={{
        p: 2,
        border: "1px solid",
        borderColor: "divider",
        borderRadius: 2,
        bgcolor: (t) =>
          t.palette.mode === "light" ? "#58a9dd30" : "transparent",
        boxShadow: (t) =>
          t.palette.mode === "dark"
            ? "0 2px 12px rgba(96,165,250,0.12)"
            : "0 2px 12px rgba(24,120,240,0.15)",
      }}
    >
      <Box component="h3" sx={{ mt: 0, mb: 2 }}>
        Управление LED
      </Box>

      <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
        <Box
          sx={{
            display: "flex",
            alignItems: "flex-start",
            gap: 2,
            flexWrap: "wrap",
          }}
        >
          {/* Адаптивная палитра */}
          <Box sx={{ flexShrink: 0 }}>
            <svg
              viewBox="0 0 380 380"
              style={{
                width: "min(380px, 60vw, 250px)", // Адаптивная ширина
                height: "auto",
                display: "block",
                cursor: "pointer",
                borderRadius: 1,
                maxWidth: "100%",
              }}
            >
              {PALETTE_TILES.map((tile, i) => (
                <polygon
                  key={i}
                  points={tile.points}
                  fill={tile.fill}
                  stroke="none"
                  onClick={() => handlePaletteClick(tile.fill)}
                />
              ))}
            </svg>

            {currentColor && (
              <Typography variant="caption" sx={{ mt: 0.5, display: "block" }}>
                Выбран:{" "}
                <span style={{ color: currentColor, fontWeight: "bold" }}>
                  {currentColor}
                </span>
              </Typography>
            )}
          </Box>

          {/* Панель управления */}
          <Box
            sx={{
              display: "flex",
              flexDirection: "column",
              gap: 2,
              minWidth: 200,
            }}
          >
            {/* HEX ввод */}
            <Box sx={{ display: "flex", gap: 1, alignItems: "center" }}>
              <TextField
                size="small"
                placeholder="#RRGGBB"
                value={hex}
                onChange={(e) =>
                  setHex(
                    e.target.value
                      .toUpperCase()
                      .replace(/[^0-9A-F]/g, "")
                      .slice(0, 6),
                  )
                }
                onKeyDown={(e) => e.key === "Enter" && handleHexSubmit()}
                sx={{ flex: 1 }}
                InputProps={{
                  startAdornment: "#",
                }}
              />
              <Button
                variant="contained"
                size="small"
                onClick={handleHexSubmit}
              >
                OK
              </Button>
            </Box>

            {/* Яркость */}
            <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
              <Typography variant="body2" sx={{ minWidth: 60 }}>
                Яркость
              </Typography>
              <input
                type="range"
                min={0}
                max={100}
                value={dragValue}
                step={1}
                onMouseDown={(e: React.MouseEvent<HTMLInputElement>) => {
                  setDragValue(
                    Number((e.target as HTMLInputElement).valueAsNumber),
                  );
                }}
                onChange={(e) => {
                  setDragValue(Number(e.target.value));
                }}
                onMouseUp={() => {
                  cmd({ brightness: (dragValue / 100).toFixed(2) }); // ← dragValue!
                }}
                onTouchStart={() => {
                  // setDragValue(serverBrightness);
                }}
                onTouchEnd={() => {
                  cmd({ brightness: (dragValue / 100).toFixed(2) }); // ← dragValue!
                }}
                style={{
                  flex: 1,
                  height: 6,
                  borderRadius: 3,
                  background:
                    "linear-gradient(to right, #58a9dd30 0%, #58a9dd30 ",
                }}
              />
              <Typography
                variant="body2"
                sx={{ minWidth: 30, textAlign: "right" }}
              >
                {dragValue}%
              </Typography>
            </Box>

            {/* Текущие значения с сервера */}
            {/* {serverBrightness !== brightness && (
              <Typography variant="caption" color="text.secondary">
                Сервер: {serverBrightness}%
              </Typography>
            )} */}
          </Box>
        </Box>
      </Box>
    </Box>
  );
};

// const LedControl = ({
//   cmd,
// }: {
//   robotId: string;
//   cmd: (c: string | Record<string, unknown>, args?: unknown) => void;
// }) => {
//   const [hex, setHex] = useState('');
//   const [currentColor, setCurrentColor] = useState<string | null>(null);
//   const [isDragging, setIsDragging] = useState(false);
//   const [dragValue, setDragValue] = useState(0);
//   const telem = connectionStore.telem;

//   const serverBrightness =
//     typeof telem['Brightness'] === 'number' ? Math.round((telem['Brightness'] as number) * 100) : 50;
//   const brightness = isDragging ? dragValue : serverBrightness;

//   const sendColor = (rgbStr: string) => {
//     cmd({ color: rgbStr });
//   };

//   const handlePaletteClick = useCallback((rgbStr: string) => {
//     const result = rgbStr.replace('rgb(', '').replace(')', '').replace(/,/g, '.');
//     setCurrentColor(rgbStr);
//     cmd({ color: result });
//   }, [cmd]);

//   const handleHexSubmit = () => {
//     const h = hex.replace(/^#/, '');
//     if (!/^[0-9A-Fa-f]{6}$/.test(h)) return;
//     const r = parseInt(h.slice(0, 2), 16);
//     const g = parseInt(h.slice(2, 4), 16);
//     const b = parseInt(h.slice(4, 6), 16);
//     sendColor(`${r}.${g}.${b}`);
//   };

//   return (
//     <Box sx={{ p: 2, border: '1px solid', borderColor: 'divider', borderRadius: 2, bgcolor: (t) => (t.palette.mode === 'light' ? '#58a9dd30' : 'transparent'), boxShadow: (t) => (t.palette.mode === 'dark' ? '0 2px 12px rgba(96,165,250,0.12)' : '0 2px 12px rgba(24,120,240,0.15)') }}>
//       <Box component="h3" sx={{ mt: 0, mb: 2 }}>Управление LED</Box>
//       <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
//         <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2, flexWrap: 'wrap' }}>
//           <Box sx={{ flexShrink: 0 }}>
//             <svg width={380} height={380} style={{ display: 'block', cursor: 'pointer' }}>
//               {PALETTE_TILES.map((tile, i) => (
//                 <polygon
//                   key={i}
//                   points={tile.points}
//                   fill={tile.fill}
//                   stroke="none"
//                   onClick={() => handlePaletteClick(tile.fill)}
//                 />
//               ))}
//             </svg>
//             {currentColor && (
//               <Typography variant="caption" sx={{ mt: 0.5, display: 'block' }}>
//                 Цвет: <span style={{ color: currentColor, fontWeight: 'bold' }}>{currentColor}</span>
//               </Typography>
//             )}
//           </Box>
//           <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, minWidth: 200 }}>
//             <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
//               <TextField
//                 size="small"
//                 placeholder="HEX (6 символов)"
//                 value={hex}
//                 onChange={(e) => setHex(e.target.value.toUpperCase().slice(0, 6))}
//                 onKeyDown={(e) => e.key === 'Enter' && handleHexSubmit()}
//                 sx={{ flex: 1 }}
//               />
//               <Button variant="contained" onClick={handleHexSubmit}>Выбрать</Button>
//             </Box>
//             <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
//               <Typography variant="body2">Яркость</Typography>
//               <input
//                 type="range"
//                 min={0}
//                 max={100}
//                 value={brightness}
//                 onMouseDown={() => {
//                   setIsDragging(true);
//                   setDragValue(serverBrightness);
//                 }}
//                 onChange={(e) => setDragValue(Number(e.target.value))}
//                 onMouseUp={() => {
//                   setIsDragging(false);
//                   cmd({ brightness: (brightness / 100).toFixed(2) });
//                 }}
//                 onTouchStart={() => {
//                   setIsDragging(true);
//                   setDragValue(serverBrightness);
//                 }}
//                 onTouchEnd={() => {
//                   setIsDragging(false);
//                   cmd({ brightness: (brightness / 100).toFixed(2) });
//                 }}
//                 style={{ width: 120 }}
//               />
//               <Typography variant="body2">{brightness}%</Typography>
//             </Box>
//           </Box>
//         </Box>
//       </Box>
//     </Box>
//   );
// };

export const ClientControl = observer(ClientControlInner);
