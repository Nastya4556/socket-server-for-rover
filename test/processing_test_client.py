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
import base64
import cv2
import numpy as np

BaseModule = mods.base.BaseModule
from src.modules.base.decorator import *

mm = ManagerModule()

@websocket_client
class ProcessingClient(BaseModule):

    ready_for_interface = False

    @classmethod
    def config_schema(cls):
        return {
            "accept_tokens": list
        }

    def __init__(self, accept_tokens=[], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.accept_tokens = accept_tokens
        self.process_message_functions["processed.telem"] = self.process_message_processed_telem
        self.process_message_functions["processed.video"] = self.process_message_processed_video

    def main_loop(self):
        message = {"processor_client.connect": {
            "id": self.connection_data["id"],
            "accept_tokens": self.accept_tokens
        }}
        msg = json.dumps(message)
        self.send_websocket(msg)

    def process_websocket(self, message):
        msg = json.loads(message)
        if "robot.telem" in msg:
            self.send_message("robot.telem", msg)

        elif "robot.video" in msg:
            frame_bytes = base64.b64decode(msg["robot.video"])

            video_message = {
                "sid": msg.get("sid"),
                "video": {"frame": frame_bytes}
            }
            self.send_message("robot.video", video_message)

    def process_message_processed_telem(self, message):
        message_json = json.dumps(message)
        self.send_websocket(message_json)

    def process_message_processed_video(self, message):
        frame_bytes = message["video"][list(message["video"].keys())[0]]
        np_arr = np.frombuffer(frame_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if frame is not None:
            cv2.imshow("YOLO Output", frame)
            cv2.waitKey(1)



class Processor(BaseModule):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.process_message_functions["robot.telem"] = self.process_message_telem

    def process_message_telem(self, message):
        processed_message = {"processed.telem":
                                {"first": message["robot.telem"]["first"] * 100,
                                "second": message["robot.telem"]["second"] * 100},
                             "auth_token": message["auth_token"],
                             "sid": message["sid"]
                             }
        self.send_message("processed.telem", processed_message)



client1 = ProcessingClient(name="ProcessingClient1",accept_tokens=["r1"], manager=mm, receivers={"robot.telem": {"names": ["Processor1"]},
                                                                                                 "robot.video": {"names": ["Yolo1"]}})
# client2 = ProcessingClient(name="ProcessingClient2",accept_tokens=["r2"], manager=mm, receivers={"robot.telem": {"names": ["Processor2"]}})


processor1 = Processor(name="Processor1",manager=mm, receivers={"processed.telem": {"names": ["ProcessingClient1"]}})
# processor2 = Processor(name="Processor2",manager=mm, receivers={"processed.telem": {"names": ["ProcessingClient2"]}})

yolo1 = YoloModule(name="Yolo1",manager=mm, receivers={"processed.video": {"names": ["ProcessingClient1"]}})

mm.connect_all_modules()
mm.start_all_threads()


while True:
    time.sleep(1)






