import asyncio
import socketio
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse


from .utils import *
from src.modules.base import BaseModule
import threading


class ClientIOModule(BaseModule):

    ready_for_interface = True

    @classmethod
    def config_schema(cls):
        return {
            "host": "str",
            "port": "int",
            "static_dir": "str"
        }

    def __init__(
        self,
        host="0.0.0.0",
        port=8000,
        static_dir="static",
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)

        self.host = host
        self.port = port
        self.static_dir = static_dir

        self.process_message_functions["robot.connected"] = self.process_message_robot_connected
        self.process_message_functions["robot.disconnected"] = self.process_message_robot_disconnected
        self.process_message_functions["robot.telemetry"] = self.process_message_robot_telemetry
        self.process_message_functions["robot.video"] = self.process_message_robot_video

        self.output_messages = [
            "robot.command",
            "data_from_client"
        ]

        self.server_thread = threading.Thread(
            target=self.run_uvicorn,
            daemon=True
        )

        # ----------------------------
        # Vault
        # ----------------------------
        self.db = Client_Vault_mixin()
        self.db.client_data = {}
        self.db.robot_data = {}

        # ----------------------------
        # Socket.IO
        # ----------------------------
        self.sio = socketio.AsyncServer(
            async_mode="asgi",
            cors_allowed_origins="*",
            callback_timeout=10
        )

        # ----------------------------
        # FastAPI
        # ----------------------------
        self.app = FastAPI(title="Client UI")

        self.app.mount(
            "/static",
            StaticFiles(directory=self.static_dir),
            name="static"
        )

        self.app.mount(
            "/assets",
            StaticFiles(directory=f"{self.static_dir}/assets"),
            name="assets"
        )

        self.app.mount(
            "/images",
            StaticFiles(directory=f"{self.static_dir}/images"),
            name="images"
        )

        @self.app.on_event("startup")
        async def on_startup():
            self.loop = asyncio.get_running_loop()

        @self.app.get("/")
        async def index():
            return FileResponse(
                f"{self.static_dir}/index.html",
                media_type="text/html"
            )

        self.asgi = socketio.ASGIApp(self.sio, self.app)

        # ----------------------------
        # Emitter
        # ----------------------------
        self.client_ns = "/client"
        self.emitter = ClientEmitter(self.db, self.sio, self.client_ns)

        # ----------------------------
        # Receiver (логика клиента)
        # ----------------------------
        self.receiver = Client_Receiver_mixin()
        self.receiver.parent = self
        self.receiver.db = self.db
        self.receiver.emitter = self.emitter

        # ----------------------------
        # Namespace
        # ----------------------------
        self.sio.register_namespace(
            ClientTelemetryNS(self.client_ns, self.receiver)
        )

        # self.main_loop()

    # =========================================================
    # Platform lifecycle
    # =========================================================

    def run_uvicorn(self):
        uvicorn.run(
            self.asgi,
            host=self.host,
            port=self.port,
            log_level="info"
        )

    def main_loop(self):
        # Сервер запускается один раз
        if not self.server_thread.is_alive():
            self.server_thread.start()




    # =========================================================
    # Platform -> Client
    # =========================================================

    async def _emit_robot_telem(self, robot_sid, telem):
        subscribers = await self.db.get_robot_subscribers(robot_sid)

        for client_sid in subscribers:
            await self.emitter.emit_to(
                client_sid,
                "telem",
                telem,
                ns=self.client_ns
            )

    async def _emit_robot_video(self, robot_sid, video):
        subscribers = await self.db.get_robot_subscribers(robot_sid)

        for client_sid in subscribers:
            await self.emitter.emit_to(
                client_sid,
                "video",
                video,
                ns=self.client_ns
            )

    # ------------------------------
    # process messages block
    # ------------------------------

    def process_message_robot_connected(self, message):
        sid = message["sid"]
        smeta = message.get("meta", {})

        self.db.robot_connections.add(sid)

        # хранилище данных робота
        self.db.robot_data.setdefault(sid, {})

        # сохраняем meta робота
        self.db.robot_data[sid]["smeta"] = smeta

        # текущее состояние (телеметрия, статус и т.п.)
        self.db.robot_data[sid].setdefault("dmeta", {})

        asyncio.run_coroutine_threadsafe(
            self.emitter.emit_client_overview(),
            self.loop
        )

    def process_message_robot_disconnected(self, message):
        sid = message["sid"]
        self.db.robot_connections.discard(sid)
        self.db.robot_data.pop(sid, None)

        asyncio.run_coroutine_threadsafe(
            self.emitter.emit_client_overview(),
            self.loop
        )

    def process_message_robot_telemetry(self, message):
        robot_sid = message["sid"]
        telem = message["telemetry"]

        self.db.robot_data.setdefault(robot_sid, {})
        self.db.robot_data[robot_sid]["telem"] = telem

        asyncio.run_coroutine_threadsafe(
            self._emit_robot_telem(robot_sid, telem),
            self.loop
        )

    def process_message_robot_video(self, message):
        robot_sid = message["sid"]
        video = message["video"]

        self.db.robot_data.setdefault(robot_sid, {})
        self.db.robot_data[robot_sid]["video"] = video

        asyncio.run_coroutine_threadsafe(
            self._emit_robot_video(robot_sid, video),
            self.loop
        )




    # =========================================================
    # Client -> Platform (override Receiver hook)
    # =========================================================

    async def client_proccess_command(self, to_sid, data, author=None):
        self.send_message(
            "robot.command",
            {
                "to_sid": to_sid,
                "data": {
                    "payload": data, "author": author
                },
            }
        )
        #new
        self.send_message(
            "data_from_client",
            {
                "to_sid": to_sid,
                "data": {
                    "payload": data, "author": author
                },
            }
        )

    async def client_subscribe(self, sid, robot_sids):
        available = await self.db.get_robot_connections()
        ans = {}

        for r_sid in robot_sids:
            if r_sid in available:
                ans[r_sid] = "ok"

                await self.db.subscribe_client_to_robot(sid, r_sid)

                # отдать последнее состояние сразу
                await self.emitter.emit_to(
                    sid,
                    "telem",
                    await self.db.robot_get_telem(r_sid),
                    ns=self.client_ns
                )
            else:
                ans[r_sid] = "no_con"

        return ans

    async def client_unsubscribe(self, sid, robot_sids):
        for r_sid in robot_sids:
            await self.db.unsubscribe_client_from_robot(sid, r_sid)
        return {r: "ok" for r in robot_sids}



