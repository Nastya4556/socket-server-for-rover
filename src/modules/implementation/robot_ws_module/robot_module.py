import asyncio
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

import threading
import uuid
from typing import Dict

from .utils import *

from src.modules.base.decorator import infinite_loop
from src.modules.base import BaseModule





def run_uvicorn(app, host, port, module):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    module._asyncio_loop = loop

    config = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="info",
        loop="asyncio"
    )
    server = uvicorn.Server(config)
    loop.run_until_complete(server.serve())


@infinite_loop(0.1)
class RobotWSModule(BaseModule):

    ready_for_interface = True

    @classmethod
    def config_schema(cls):
        return {
            "host": "str",
            "port": "int",
        }

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 5000,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)

        self.process_message_functions["robot.command"] = self.process_message_robot_command

        self.output_messages = [
            "robot.telemetry",
            "robot.video",
            # "robot.file",
            "robot.connected",
            "robot.disconnected"
        ]

        self.db = Robot_Vault_mixin()

        self.app = FastAPI(title="Robot WS")
        self.host = host
        self.port = port

        self._connections: Dict[str, WebSocket] = {}
        self._connections_lock = asyncio.Lock()

        @self.app.websocket("/robot/ws")
        async def robot_ws_endpoint(websocket: WebSocket):
            await websocket.accept()

            try:
                first = await websocket.receive_json()
            except Exception:
                await websocket.close()
                return

            if not isinstance(first, dict) or first.get("event") != "connect":
                await websocket.close()
                return

            payload = first.get("data", {}) or {}
            auth = payload.get("auth")
            sid = payload.get("sid") or str(uuid.uuid4())

            websocket.scope["sid"] = sid

            async with self._connections_lock:
                self._connections[sid] = websocket

            try:
                await self.robot_proccess_connection(websocket, auth)
            except Exception:
                async with self._connections_lock:
                    self._connections.pop(sid, None)
                await websocket.close()
                return

            try:
                while True:
                    msg = await websocket.receive_json()

                    if not isinstance(msg, dict):
                        continue

                    event = msg.get("event")
                    data = msg.get("data")

                    if event == "telem":
                        await self.robot_pass_telem(websocket, data)

                    elif event == "video":
                        await self.robot_pass_video(websocket, data)

                    elif event == "file":
                        await self.robot_pass_file(websocket, data)

                    elif event == "disconnect":
                        break
                    else:
                        continue

            except WebSocketDisconnect:
                pass
            except Exception:
                pass
            finally:
                async with self._connections_lock:
                    self._connections.pop(sid, None)

                await self.robot_proccess_disconnection(websocket)

        self.server_thread = threading.Thread(
            target=run_uvicorn,
            args=(self.app, self.host, self.port, self),
            daemon=True
        )

    def main_loop(self):
        # Сервер запускается один раз
        if not self.server_thread.is_alive():
            self.server_thread.start()

    async def send_to_sid(self, sid: str, event: str, data):
        async with self._connections_lock:
            ws = self._connections.get(sid)

        if ws is None:
            return False

        try:
            await ws.send_json({"event": event, "data": data})
            return True
        except Exception:
            async with self._connections_lock:
                self._connections.pop(sid, None)
            return False

    async def send_to_ws(self, websocket: WebSocket, event: str, data):
        sid = websocket.scope.get("sid")
        if sid is None:
            return False
        try:
            await websocket.send_json({"event": event, "data": data})
            return True
        except Exception:
            async with self._connections_lock:
                stored = self._connections.get(sid)
                if stored is websocket:
                    self._connections.pop(sid, None)
            return False

    async def robot_pass_telem(self, websocket: WebSocket, data):
        sid = websocket.scope["sid"]
        await self.db.robot_set_telem(sid, data)

        self.send_message(
            "robot.telemetry",
            {
                "sid": sid,
                "telemetry": data
            }
        )


    async def robot_pass_video(self, websocket: WebSocket, data):
        sid = websocket.scope["sid"]
        await self.db.robot_set_video(sid, data)

        # frame_key = list(data['payload'].keys())[0]
        # frame_bytes = base64.b64decode(data['payload'][frame_key])
        # frame = cv2.imdecode(
        #     np.frombuffer(frame_bytes, dtype=np.uint8),
        #     cv2.IMREAD_COLOR
        # )
        # data['payload'][frame_key] = frame

        self.send_message(
            "robot.video",
            {
                "sid": sid,
                "video": data
            }
        )

    async def robot_pass_file(self, websocket: WebSocket, data):
        sid = websocket.scope["sid"]
        await self.db.robot_set_file(sid, data)

        self.send_message(
            "robot.file",
            {
                "sid": sid,
                "file": data
            }
        )

    async def robot_proccess_connection(self, websocket: WebSocket, auth):
        sid = websocket.scope["sid"]

        await self.db.robot_registry(sid, auth)

        await self.send_to_ws(websocket, "token_ask", None)

        await self.send_to_ws(websocket, "heartbeat", ["d_meta", "Ready"])

        self.send_message(
            "robot.connected",
            {
                "sid": sid,
                "meta": auth
            }
        )

    async def robot_proccess_disconnection(self, websocket: WebSocket):
        sid = websocket.scope["sid"]
        await self.db.robot_delete(sid)

        self.send_message(
            "robot.disconnected",
            {"sid": sid}
        )

    def process_message_robot_command(self, message):
        sid = message["to_sid"]
        data = message["data"]

        if hasattr(self, "_asyncio_loop") and self._asyncio_loop is not None:
            asyncio.run_coroutine_threadsafe(
                self.send_to_sid(sid, "command", data),
                self._asyncio_loop
            )
