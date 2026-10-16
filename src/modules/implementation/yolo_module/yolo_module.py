import json
import copy

from pathlib import Path
from ultralytics import YOLO
import numpy as np
import cv2

from src.modules.base.decorator import infinite_loop
from src.modules.base import BaseModule

@infinite_loop(0.1)
class YoloModule(BaseModule):
    def __init__(self, *args, **kwargs,):
        super().__init__(*args, **kwargs)
        # Загрузка модели YOLOv8

        print("[info] YOLO model is loading")
        folder_path = Path(__file__).parent
        weights_path = folder_path / "arrow_model.pt"
        params_path = folder_path / "params.json"
        self.model = YOLO(weights_path.as_posix())

        with open(params_path, 'r') as f:
            data = json.load(f)

        self.min_size = data['min_size']

        self.process_message_functions["robot.video"] = self.process_message_robot_video

        print("[info] YOLO model is loaded")


    def socket_recieve(self):
        self.socket.emit()

    def main_loop(self):
        # if not self._queue.empty():
        #     signature, message = self._queue.get()
        #     self.process_message(signature, message)
        pass
    #
    # def receive_message(self, signature, message):
    #     msg = signature, message
    #     self._queue.put(msg)

    def process_message_robot_video(self, msg):
        message = copy.deepcopy(msg)

        robot_sid = message["sid"]
        frame_bytes = message['video'][list(message['video'].keys())[0]]

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

        corner_margin = 5  # пикселей для игнорирования углов

        if results[0].boxes:

            for box in results[0].boxes:

                class_id = int(box.cls[0])
                conf = float(box.conf[0])
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                class_name = classes_names[class_id]

                # ---------------- УГЛОВАЯ ФИЛЬТРАЦИЯ ----------------

                touches_top_left = x1 <= corner_margin and y1 <= corner_margin
                touches_top_right = x2 >= (w - corner_margin) and y1 <= corner_margin
                touches_bottom_left = x1 <= corner_margin and y2 >= (h - corner_margin)
                touches_bottom_right = x2 >= (w - corner_margin) and y2 >= (h - corner_margin)

                if (
                        touches_top_left
                        or touches_top_right
                        or touches_bottom_left
                        or touches_bottom_right
                ):
                    continue

                # ---------------- ПЛОЩАДЬ ----------------

                object_size = (x2 - x1) * (y2 - y1)
                area_percent = (object_size / image_size) * 100

                # ---------------- СМЕЩЕНИЕ ОТНОСИТЕЛЬНО ЦЕНТРА ----------------

                box_center_x = (x1 + x2) / 2
                offset_norm = (box_center_x - frame_center_x) / frame_center_x
                # теперь в диапазоне [-1 ... +1]

                # ---------------- ВЫБОР ЛУЧШЕГО ОБЪЕКТА ----------------

                if conf > best_conf:
                    best_conf = conf
                    best_class_name = class_name
                    best_area_percent = area_percent
                    best_offset_norm = offset_norm

                # ---------------- ЦВЕТ ----------------

                if class_name == "class0":
                    color = (0, 0, 255)
                elif class_name == "class1":
                    color = (255, 0, 0)
                else:
                    color = (0, 255, 0)

                # ---------------- РИСОВАНИЕ ----------------

                cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)

                label = (
                    f"{class_name} | "
                    f"{conf:.2f} | "
                    f"{area_percent:.1f}% | "
                    f"off:{offset_norm:.2f}"
                )

                (tw, th), _ = cv2.getTextSize(
                    label,
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    1
                )

                cv2.rectangle(
                    image,
                    (x1, y1 - th - 6),
                    (x1 + tw, y1),
                    color,
                    -1
                )

                cv2.putText(
                    image,
                    label,
                    (x1, y1 - 4),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 255),
                    1,
                    cv2.LINE_AA
                )

                detected = True

        # ---------------- ОТПРАВКА YOLO.DETECT ----------------

        if detected and best_class_name is not None:
            detect_message = {
                'to_sid': robot_sid,
                'data': {
                    'class': best_class_name,
                    'area_percent': round(best_area_percent, 2),
                    'center_offset_norm': round(best_offset_norm, 3)
                },
                'author': f'{self.name}'
            }

            self.send_message("yolo.detect", detect_message)

        # ---------------- ОТПРАВКА КАДРА ----------------

        success, encoded_image = cv2.imencode('.png', image)
        if not success:
            return

        message['video'][list(message['video'].keys())[0]] = encoded_image.tobytes()
        self.send_message('processed.video', message)