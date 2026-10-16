import json
from pathlib import Path

from src.modules.base.decorator import infinite_loop
from src.modules.base import BaseModule

@infinite_loop(0.1)
class YoloControlModule(BaseModule):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        print("[info] YOLO Control module loading")

        folder_path = Path(__file__).parent
        config_path = folder_path / "commands.json"

        with open(config_path, "r") as f:
            cfg = json.load(f)

        self.target_area = cfg["target_area_percent"]
        self.center_tol = cfg["center_tolerance"]
        self.center_bias = cfg["center_bias"]
        self.alpha = cfg["smoothing_alpha"]
        self.lost_limit = cfg["lost_frames_limit"]

        self.active = False
        self.smoothed_offset = 0.0
        self.lost_frames = 0
        self.current_sid = None

        # --- управление переключением ---
        self.last_command = None
        self.pending_command = None
        self.wait_stop_cycle = False

        print("[info] YOLO Control module loaded")

    # --------------------------------------------------

    def socket_recieve(self):
        self.socket.emit()

    # --------------------------------------------------

    def main_loop(self):

        # обработка безопасного переключения
        if self.wait_stop_cycle:
            self._send_raw_command(self.pending_command)
            self.last_command = self.pending_command
            self.pending_command = None
            self.wait_stop_cycle = False

        # проверка потери
        if self.active:
            self.lost_frames += 1

            if self.lost_frames > self.lost_limit:
                print("[YOLO_CONTROL] Object lost → stop")
                self.force_stop()
                self.active = False

        # if not self._queue.empty():
        #     signature, message = self._queue.get()
        #     self.process_message(signature, message)

    # --------------------------------------------------
    #
    # def receive_message(self, signature, message):
    #     self._queue.put((signature, message))

    # --------------------------------------------------

    def process_message(self, signature, msg):

        # ---------------- ROBOT.CONTROL ----------------

        if signature == "robot.control":

            command = msg.get("control")

            if command == "start":
                self.active = True
                self.lost_frames = 0
                self.smoothed_offset = 0.0
                self.last_command = None
                print("[YOLO_CONTROL] Activated")

            elif command == "stop":
                self.active = False
                self.force_stop()
                print("[YOLO_CONTROL] Stopped manually")

            return

        # ---------------- YOLO.DETECT ----------------

        if signature != "yolo.detect":
            return

        if not self.active:
            return

        robot_sid = msg.get("to_sid")
        self.current_sid = robot_sid

        data = msg.get("data", {})
        area = data.get("area_percent")
        offset = data.get("center_offset_norm")

        if area is None or offset is None:
            return

        self.lost_frames = 0

        offset_corrected = offset + self.center_bias

        self.smoothed_offset = (
            self.alpha * offset_corrected
            + (1 - self.alpha) * self.smoothed_offset
        )

        if area >= self.target_area:
            print("[YOLO_CONTROL] Target reached → stop")
            self.force_stop()
            self.active = False
            return

        if abs(self.smoothed_offset) > self.center_tol:

            if self.smoothed_offset > 0:
                new_command = "up"
            else:
                new_command = "down"
        else:
            new_command = "forward"

        self.safe_send_command(new_command)

    # --------------------------------------------------
    # ----------- SAFE COMMAND SWITCH ------------------
    # --------------------------------------------------

    def safe_send_command(self, new_command):

        if not self.current_sid:
            return

        if self.last_command is None:
            self._send_raw_command(new_command)
            self.last_command = new_command
            return

        if new_command == self.last_command:
            return

        self._send_raw_command("stop")
        self.pending_command = new_command
        self.wait_stop_cycle = True

    # --------------------------------------------------

    def force_stop(self):
        self._send_raw_command("stop")
        self.last_command = "stop"
        self.pending_command = None
        self.wait_stop_cycle = False

    # --------------------------------------------------

    def _send_raw_command(self, com):

        if not self.current_sid:
            return

        command_message = {
            'to_sid': self.current_sid,
            'data': {
                'payload': {
                    'com': com
                },
                'author': f'{self.name}'
            }
        }

        self.send_message("robot.command", command_message)
