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
import base64
import io
import time
import datetime
import numpy as np
from PIL import Image
import cv2

BaseModule = mods.base.BaseModule
from src.modules.base.decorator import *

TZ = datetime.timezone(datetime.timedelta(hours=3))

mm = ManagerModule()

@websocket_client
@infinite_loop(1)
class Robot(BaseModule):

    ready_for_interface = False

    @classmethod
    def config_schema(cls):
        return {
            "auth_token": str
        }


    def __init__(self, auth_token, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auth_token = auth_token
        self.robot_connected = False

    def main_loop(self):
        # if not self.connected:
        #     return
        #
        # if not self.robot_connected:
        #     message = {"robot.connect": {
        #         "id": self.connection_data["id"],
        #         "auth_token": self.auth_token
        #     }}
        #     msg = json.dumps(message)
        #     self.send_websocket(msg)
        #     self.robot_connected = True
        #
        # telem = {"robot.telem": {"first": np.random.randint(0,100),
        #                         "second": np.random.randint(0, 100)},
        #          "sid": self.connection_data["id"]
        #          }
        # telem_json = json.dumps(telem)
        # self.send_websocket(telem_json)

        if not self.connected:
            return

        img = Image.open("test_img.jpg")
        img.thumbnail((640, 480))
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=60)
        img_enc = base64.b64encode(buffer.getvalue()).decode("utf-8")
        video_json = json.dumps({
            "robot.video": img_enc,
            "timestamps": {
                "(1)robot_send": datetime.datetime.now(TZ).strftime("%X:%f")
            }
        })
        self.send_websocket(video_json)


    def process_websocket(self, message):
        msg = json.loads(message)
        if "processed.telem" in msg:
            print(self.name, msg)

        elif "processed.video" in msg:
            now = datetime.datetime.now(TZ)
            msg["timestamps"]["(4)robot_receive"] = now.strftime("%X:%f")

            fmt = "%H:%M:%S:%f"
            today = datetime.date.today()

            t_send = datetime.datetime.strptime(msg["timestamps"]["(1)robot_send"], fmt).replace(
                year=today.year, month=today.month, day=today.day)
            t_receive = datetime.datetime.strptime(msg["timestamps"]["(4)robot_receive"], fmt).replace(
                year=today.year, month=today.month, day=today.day)

            time_elapsed = (t_receive - t_send).total_seconds()
            print(f"{msg['timestamps']}, time elapsed: {time_elapsed:.3f}s")

            # Декодируем base64 обратно в кадр
            img_b64 = msg["processed.video"]["robot.video"]
            frame_bytes = base64.b64decode(img_b64)
            np_arr = np.frombuffer(frame_bytes, np.uint8)
            image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if image is not None:
                cv2.imshow("YOLO Output", image)
                cv2.waitKey(1)

    def on_disconnect(self):
        self.robot_connected = False

robot1 = Robot(name="Robot1", auth_token="r1", manager=mm, host="127.0.0.1", port=8080)
# robot2 = Robot(name="Robot2", auth_token="r2", manager=mm)


mm.start_all_threads()


while True:
    time.sleep(1)






