import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Box,
  Button,
  Card,
  Typography,
  IconButton,
  Menu,
  MenuItem,
} from "@mui/material";
import MoreVertIcon from "@mui/icons-material/MoreVert";
import { observer } from "mobx-react-lite";
import { connectionStore } from "@entities/connection";
import { TelemTable, VideoList } from "@entities/connection";
import {
  subscribe,
  unsubscribe,
  sendCommand,
  sendFileCommand,
} from "@features/socket";
import { ClientControl } from "@features/client-control";
import { ClientViewLoader } from "@shared/ui/ClientViewLoader";

const LOADER_MS = 250;

const ClientViewPageInner = () => {
  const { ip } = useParams<{ ip: string }>();
  const navigate = useNavigate();
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);
  const [displayedIp, setDisplayedIp] = useState<string | null>(null);

  useEffect(() => {
    if (!ip) return;
    const t = setTimeout(() => setDisplayedIp(ip), LOADER_MS);
    return () => clearTimeout(t);
  }, [ip]);

  useEffect(() => {
    if (!ip) return;
    connectionStore.markVideoSwitch();
    if (
      connectionStore.currentClientIp &&
      connectionStore.currentClientIp !== ip
    ) {
      unsubscribe(connectionStore.currentClientIp);
      connectionStore.clearVideo();
      connectionStore.setTelem({});
    }
    connectionStore.setCurrentClient(ip);
    connectionStore.setTelem({});
    connectionStore.clearVideo();
    subscribe(ip);
    sendCommand(ip, "pass");

    return () => {
      connectionStore.markVideoSwitch();
      unsubscribe(ip);
      connectionStore.setCurrentClient(null);
      connectionStore.setTelem({});
      connectionStore.clearVideo();
    };
  }, [ip]);

  useEffect(() => {
    if (ip && connectionStore.robots[ip] === undefined) {
      navigate("/", { replace: true });
    }
  }, [ip, navigate]);

  if (!ip) return null;

  if (ip !== displayedIp) return <ClientViewLoader />;

  const robot = connectionStore.robots[ip] ?? null;

  if (!robot) return null;

  const handleBack = () => {
    connectionStore.markVideoSwitch();
    unsubscribe(ip);
    connectionStore.setCurrentClient(null);
    connectionStore.setTelem({});
    connectionStore.clearVideo();
    navigate("/");
  };

  return (
    <Box
      key={ip}
      sx={{
        display: "flex",
        flexDirection: "column",
        gap: 1.5,
        flex: 1,
        minHeight: 0,
      }}
    >
      <Card
        sx={{
          p: 2,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexShrink: 0,
        }}
      >
        <Typography variant="h6">
          Клиент{" "}
          <Typography component="span" sx={{ fontFamily: "monospace" }}>
            {ip}
          </Typography>
        </Typography>
        <Button variant="contained" onClick={handleBack}>
          Назад к сводке
        </Button>
      </Card>

      <Box
        sx={{ display: "flex", gap: 1.5, width: "100%", flex: 1, minHeight: 0 }}
      >
        <Box
          sx={{
            width: "100%",
            maxWidth: 450,
            flexShrink: 0,
            minHeight: 0,
            display: "flex",
            flexDirection: "column",
            gap: 1.5,
          }}
        >
          <ClientControl robotId={ip} robot={robot} />

          <Card
            sx={{
              p: 2,
              flex: 1,
              minHeight: 0,
              display: "flex",
              flexDirection: "column",
            }}
          >
            <Typography variant="h6" gutterBottom>
              Телеметрия
            </Typography>

            <Box sx={{ flex: 1, minHeight: "150px", overflow: "auto" }}>
              <TelemTable />
            </Box>
          </Card>
        </Box>

        <Box
          sx={{
            flex: 1,
            minWidth: 0,
            minHeight: 0,
            display: "flex",
            flexDirection: "column",
            gap: 1.5,
            overflow: "hidden",
          }}
        >
          <Card
            sx={{
              p: 2,
              flex: 1,
              minHeight: 0,
              display: "flex",
              flexDirection: "column",
              overflow: "hidden",
            }}
          >
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                mb: 1.5,
                flexShrink: 0,
              }}
            >
              <Typography variant="h6">Видео</Typography>
              {(robot?.posibilities?.video === true ||
                Object.keys(connectionStore.videoFrames).length > 0) && (
                <>
                  <IconButton
                    size="small"
                    onClick={(e) => setMenuAnchor(e.currentTarget)}
                    aria-label="Меню взаимодействия"
                  >
                    <MoreVertIcon />
                  </IconButton>
                  <Menu
                    anchorEl={menuAnchor}
                    open={Boolean(menuAnchor)}
                    onClose={() => setMenuAnchor(null)}
                    anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
                    transformOrigin={{ vertical: "top", horizontal: "right" }}
                    slotProps={{
                      paper: {
                        sx: (t) => {
                          const isDark = t.palette.mode === "dark";
                          const glow = isDark
                            ? "0 0 12px rgba(96,165,250,0.06), 0 0 20px rgba(236,72,153,0.03)"
                            : "0 2px 12px rgba(24,120,240,0.15)";
                          return {
                            bgcolor: `${isDark ? "#0c0f1c" : "#f6f8fa"} !important`,
                            backdropFilter: `${isDark ? "blur(8px)" : "none"} !important`,
                            border: `1px solid ${t.palette.divider} !important`,
                            boxShadow: `${glow} !important`,
                          };
                        },
                      },
                    }}
                  >
                    <MenuItem
                      onClick={() => {
                        document.getElementById("client-file-input")?.click();
                        setMenuAnchor(null);
                      }}
                    >
                      Код (загрузить .py)
                    </MenuItem>
                    <MenuItem
                      onClick={() => {
                        sendFileCommand(ip, "log");
                        setMenuAnchor(null);
                      }}
                    >
                      Логи
                    </MenuItem>
                    <MenuItem
                      onClick={() => {
                        sendFileCommand(ip, "error");
                        setMenuAnchor(null);
                      }}
                    >
                      Ошибки
                    </MenuItem>
                    <MenuItem
                      onClick={() => {
                        sendFileCommand(ip, "code");
                        setMenuAnchor(null);
                      }}
                    >
                      Код
                    </MenuItem>
                  </Menu>
                </>
              )}
            </Box>

            <input
              id="client-file-input"
              type="file"
              accept=".py"
              style={{ display: "none" }}
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (!file || !ip) return;
                const reader = new FileReader();
                reader.onload = () => {
                  sendCommand(ip, "uploadFile", reader.result as string);
                };
                reader.readAsText(file);
                e.target.value = "";
              }}
            />

            <Box sx={{ flex: 1, minHeight: 0, overflow: "hidden" }}>
              <VideoList />
            </Box>
          </Card>
        </Box>
      </Box>
    </Box>
  );
};

export const ClientViewPage = observer(ClientViewPageInner);
