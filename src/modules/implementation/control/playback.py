import json
import time
import base64
from pathlib import Path

from src.modules.base.decorator import infinite_loop
from src.modules.base import BaseModule

@infinite_loop(0.001)
class VideoPlaybackModule(BaseModule):

    @classmethod
    def config_schema(cls):
        return {
            "bag_path": "str"
        }


    def __init__(self, bag_path, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.root_dir = Path.cwd()
        self.bag_path = self.root_dir / bag_path

        with open(self.bag_path, "r") as f:
            self.bag_data = json.load(f)

        self.playing = False
        self.start_time = None
        self.index = 0

    def main_loop(self):
        if self.index >= len(self.bag_data):
            self.playing = False
            self.index = 0
            return

        item = self.bag_data[self.index]

        if self.index == 0:
            self.start_time = time.time()
            self.first_timestamp = item["timestamp"]

        # соблюдение тайминга
        current_real_time = time.time() - self.start_time
        bag_relative_time = item["timestamp"] - self.first_timestamp

        if current_real_time >= bag_relative_time:

            frame_bytes = base64.b64decode(item["data"])

            self.send_message("robot.video", {
                "video": {
                    "rgb": frame_bytes
                }
            })

            self.index += 1
    #
    # def receive_message(self, signature, message):
    #     self._queue.put((signature, message))

    def process_message(self, signature, msg):

        if signature != "video.play":
            return

        command = msg.get("play")

        if command == "start":
            self.playing = True
            self.index = 0

        elif command == "stop":
            self.playing = False
            self.index = 0