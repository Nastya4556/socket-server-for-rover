from src import modules as mods

ManagerModule = mods.base.ManagerModule
CarModule = mods.implementation.CarModule
ClientIOModule = mods.implementation.ClientIOModule
ConsoleLogModule = mods.implementation.ConsoleLogModule
ControllerModule = mods.implementation.CarControllerModule
RobotIOModule = mods.implementation.RobotWSModule
SenderModule = mods.implementation.SenderModule
SqliteModule = mods.implementation.SqliteModule
ProcessorModule = mods.implementation.ProcessorModule
WebInterfaceModule = mods.implementation.WebInterfaceModule
UnrealCarModule = mods.implementation.UnrealCarModule
YoloModule = mods.implementation.YoloModule

import time

BaseModule = mods.base.BaseModule
from src.modules.base.decorator import *

mm = ManagerModule()

@websocket_server
class ProcessingServer(BaseModule):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    def process_websocket(self, message):
        msg = json.loads(message)
        if "robot.connect" in msg:
            id = msg["robot.connect"]["id"]
            auth_token = msg["robot.connect"]["auth_token"]
            self._connected[id]["auth_token"] = auth_token
            self._connected[id]["type"] = "robot"
            # print(self._connected)

        elif "processor_client.connect" in msg:
            accept_tokens = msg["processor_client.connect"]["accept_tokens"]
            id = msg["processor_client.connect"]["id"]
            self._connected[id]["accept_tokens"] = accept_tokens
            self._connected[id]["type"] = "processor_client"
            # print(self._connected)

        elif "robot.telem" in msg:
            sid = msg["sid"]
            auth_token = self._connected[sid]["auth_token"]
            if auth_token is None:
                return

            self._send_to_processor(auth_token, "robot.telem", msg)

        elif "robot.video" in msg:
            sid = msg["sid"]
            auth_token = self._connected[sid]["auth_token"]
            if auth_token is None:
                return

            self._send_to_processor(auth_token, "robot.video", msg)

        elif "processed.telem" in msg:
            auth_token = msg["auth_token"]
            self._send_to_robot(auth_token, msg)

    def _send_to_processor(self, auth_token, signature, msg):
        for id, client in self._connected.items():
            if client.get("type") == "processor_client":
                for token in client["accept_tokens"]:
                    if token == auth_token:
                        sid = client["id"]
                        # temp и сид и токен
                        message =   {signature: msg[signature],
                                    "auth_token": auth_token,
                                     "sid": sid}
                        self.send_websocket(id, json.dumps(message))
                        return

    def _send_to_robot(self, auth_token, msg):
        for id, client in self._connected.items():
            if client.get("type") == "robot":
                if client.get("auth_token") == auth_token:
                    sid = client["id"]
                    message = {"processed.telem": msg["processed.telem"],
                               "sid": sid}
                    self.send_websocket(id, json.dumps(message))
                    return





server = ProcessingServer(name="ProcessingServer", manager=mm)


mm.start_all_threads()


while True:
    time.sleep(1)






