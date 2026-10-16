import asyncio
import socketio
import uvicorn
from fastapi import FastAPI

import threading
import time


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
class RobotIOModule(Robot_Receiver_mixin, BaseModule):


    ready_for_interface = True

    @classmethod
    def config_schema(cls):
        return {
            "host": "str",
            "port": "int",
        }

    def __init__(
        self,
        host="127.0.0.1",
        port=5000,
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

        # --- socket.io ---
        self.sio = socketio.AsyncServer(
            async_mode="asgi",
            cors_allowed_origins="*",

            callback_timeout=10
        )

        self.app = FastAPI(title="Robot IO")
        self.asgi = socketio.ASGIApp(self.sio, self.app)

        # namespace
        self.sio.register_namespace(
            RobotTelemetryNS("/robot", self)
        )

        self.host = host
        self.port = port

        self.server_thread = threading.Thread(
            target=run_uvicorn,
            args=(self.asgi, self.host, self.port, self),
            daemon=True
        )

    def main_loop(self):
        # сервер запускается ОДИН РАЗ
        if not self.server_thread.is_alive():
            self.server_thread.start()


    async def robot_pass_telem(self, sid, data):
        await self.db.robot_set_telem(sid, data)

        self.send_message(
            "robot.telemetry",
            {
                "sid": sid,
                "telemetry": data
            }
        )

    async def robot_pass_video(self, sid, data):
        self.send_message(
            "robot.video",
            {
                "sid": sid,
                "video": data
            }
        )

    async def robot_pass_file(self, sid, data):
        self.send_message(
            "robot.file",
            {
                "sid": sid,
                "file": data
            }
        )

    async def robot_proccess_connection(self, sid, auth):
        await self.db.robot_registry(sid, auth)

        await self.sio.emit(
            "token_ask",
            None,
            to=sid,
            namespace="/robot"
        )

        await self.sio.emit(
            "heartbeat",
            ['d_meta', 'Ready'],

            to=sid,
            namespace="/robot"
        )

        self.send_message(
            "robot.connected",
            {
                "sid": sid,
                "meta": auth
            }
        )

    async def robot_proccess_disconnection(self, sid):
        await self.db.robot_delete(sid)

        self.send_message(
            "robot.disconnected",
            {"sid": sid}
        )


    def process_message_robot_command(self, message):
        sid = message["to_sid"]
        data = message["data"]
        # time.sleep(1)
        asyncio.run_coroutine_threadsafe(
            self.sio.emit(
                "command",
                data,
                to=sid,
                namespace="/robot"
            ),
            self._asyncio_loop
        )