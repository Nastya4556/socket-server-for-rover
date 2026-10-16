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
from src.modules.base.decorator import *

import json
import base64
import numpy as np
import cv2
import time
import datetime


TZ = datetime.timezone(datetime.timedelta(hours=3))

@websocket_server
class YoloWs(YoloModule):
    def __init__(self, *args, **kwargs,):
        super().__init__(*args, **kwargs)

    def process_websocket(self, message):
        msg = json.loads(message)
        if "timestamps" in msg:
            msg["timestamps"]["(2)yolo_receive"] = datetime.datetime.now(TZ).strftime("%X:%f")
            # print(msg["timestamps"])
        if "robot.video" in msg:
            img_b64 = msg["robot.video"]
            frame_bytes = base64.b64decode(img_b64)
            np_arr = np.frombuffer(frame_bytes, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            if frame is None:
                return

            results = self.model(frame, verbose=False)

            image = results[0].orig_img
            h, w = image.shape[:2]
            image_size = h * w
            frame_center_x = w / 2
            classes_names = results[0].names

            detected = False
            best_class_name = None
            best_area_percent = 0.0
            best_offset_norm = 0.0
            best_conf = -1
            corner_margin = 5

            if results[0].boxes:
                for box in results[0].boxes:
                    class_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    class_name = classes_names[class_id]

                    touches_top_left = x1 <= corner_margin and y1 <= corner_margin
                    touches_top_right = x2 >= (w - corner_margin) and y1 <= corner_margin
                    touches_bottom_left = x1 <= corner_margin and y2 >= (h - corner_margin)
                    touches_bottom_right = x2 >= (w - corner_margin) and y2 >= (h - corner_margin)

                    if touches_top_left or touches_top_right or touches_bottom_left or touches_bottom_right:
                        continue

                    object_size = (x2 - x1) * (y2 - y1)
                    area_percent = (object_size / image_size) * 100
                    box_center_x = (x1 + x2) / 2
                    offset_norm = (box_center_x - frame_center_x) / frame_center_x

                    if conf > best_conf:
                        best_conf = conf
                        best_class_name = class_name
                        best_area_percent = area_percent
                        best_offset_norm = offset_norm

                    color = (0, 0, 255) if class_name == "class0" else (255, 0, 0) if class_name == "class1" else (0,
                                                                                                                   255,
                                                                                                                   0)
                    cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)

                    label = f"{class_name} | {conf:.2f} | {area_percent:.1f}% | off:{offset_norm:.2f}"
                    (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                    cv2.rectangle(image, (x1, y1 - th - 6), (x1 + tw, y1), color, -1)
                    cv2.putText(image, label, (x1, y1 - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1,
                                cv2.LINE_AA)
                    detected = True

            if detected and best_class_name is not None:
                detect_message = {
                    'data': {
                        'class': best_class_name,
                        'area_percent': round(best_area_percent, 2),
                        'center_offset_norm': round(best_offset_norm, 3)
                    },
                    'author': f'{self.name}'
                }
                # self.send_message("yolo.detect", detect_message)

            success, encoded_image = cv2.imencode('.jpg', image)
            if not success:
                return

            timestamps = msg["timestamps"]
            timestamps["(3)yolo_send"] = datetime.datetime.now(TZ).strftime("%X:%f")

            out_b64 = base64.b64encode(encoded_image.tobytes()).decode("utf-8")
            # self.send_message('processed.video', {"robot.video": out_b64})
            json_msg = json.dumps({
                'processed.video': {"robot.video": out_b64},
                'timestamps': timestamps
            })
            self.send_websocket_all(json_msg)

            # cv2.imshow("YOLO Output", image)
            # cv2.waitKey(1)





HOST = "0.0.0.0"
PORT = 8080

mm = ManagerModule()

yolo = YoloWs(name="Yolo", manager=mm, host=HOST, port=PORT)

mm.start_all_threads()


while True:
    time.sleep(1)