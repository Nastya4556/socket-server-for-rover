import json
import time
import copy
import base64
import cv2
import numpy as np
from pathlib import Path
from datetime import datetime

from src.modules.base.decorator import infinite_loop
from src.modules.base import BaseModule

@infinite_loop(0.01)
class VideoRecordModule(BaseModule):

    def config_schema(cls):
        return {
            "records_dir": "str"
        }

    def __init__(self, records_dir="files", *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.root_dir = Path.cwd()
        self.records_dir = self.root_dir / records_dir
        self.records_dir.mkdir(exist_ok=True)

        self.recording = False
        self.current_folder = None

        self.bag_data = []
        self.frames_buffer = []
        self.frame_times = []


    def main_loop(self):
    #     if not self._queue.empty():
    #         signature, message = self._queue.get()
    #         self.process_message(signature, message)
        pass
    #
    # def receive_message(self, signature, message):
    #     self._queue.put((signature, message))

    # =========================================================

    def start_recording(self):
        if self.recording:
            return  # игнор повторного start

        timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.current_folder = self.records_dir / f"{self.name}_{timestamp_str}"
        self.current_folder.mkdir()

        self.bag_data = []
        self.frames_buffer = []
        self.frame_times = []

        self.recording = True

        print(f"[RECORDER] Started recording: {timestamp_str}")

    def stop_recording(self):
        if not self.recording:
            return  # игнор stop если не записываем

        print("[RECORDER] Stopping recording...")

        # ---------------------------------------------
        bag_path = self.current_folder / "bag.json"
        with open(bag_path, "w") as f:
            json.dump(self.bag_data, f)

        # ---------------------------------------------
        fps = 20.0  # fallback

        if len(self.frame_times) > 1:
            deltas = [
                t2 - t1
                for t1, t2 in zip(self.frame_times[:-1], self.frame_times[1:])
            ]

            # убираем возможные выбросы через медиану
            deltas_sorted = sorted(deltas)
            median_delta = deltas_sorted[len(deltas_sorted) // 2]

            if median_delta > 0:
                fps = 1.0 / median_delta

        # ---------------------------------------------
        if self.frames_buffer:

            height, width = self.frames_buffer[0].shape[:2]
            video_path = str(self.current_folder / "video.mp4")

            video_writer = cv2.VideoWriter(
                video_path,
                cv2.VideoWriter_fourcc(*"mp4v"),
                fps,
                (width, height)
            )

            for frame in self.frames_buffer:
                video_writer.write(frame)

            video_writer.release()

            print(f"[RECORDER] Video saved with FPS={fps:.2f}")

        # ---------------------------------------------
        self.recording = False
        self.current_folder = None
        self.bag_data = []
        self.frames_buffer = []
        self.frame_times = []

        print("[RECORDER] Recording stopped")

    # =========================================================

    def process_message(self, signature, msg):

        # ---------------------------------------------

        if signature == "video.record":
            command = msg.get("record")

            if command == "start":
                self.start_recording()

            elif command == "stop":
                self.stop_recording()

            return

        # ---------------------------------------------

        if signature == "robot.video" and self.recording:

            timestamp = time.time()
            message = copy.deepcopy(msg)

            frame_bytes = message['video'][list(message['video'].keys())[0]]

            # --- BAG ---
            encoded = base64.b64encode(frame_bytes).decode("utf-8")

            self.bag_data.append({
                "timestamp": timestamp,
                "signature": "robot.video",
                "data": encoded
            })

            # --- FRAME BUFFER ---
            np_arr = np.frombuffer(frame_bytes, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if frame is None:
                return  # если кадр битый

            self.frames_buffer.append(frame)
            self.frame_times.append(timestamp)