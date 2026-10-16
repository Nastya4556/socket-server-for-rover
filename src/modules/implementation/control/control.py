import copy
from src.modules.base.decorator import infinite_loop
from src.modules.base import BaseModule

@infinite_loop(0.01)
class ControlModule(BaseModule):

    def main_loop(self):
        # if not self._queue.empty():
        #     signature, message = self._queue.get()
        #     self.process_message(signature, message)
        pass


    # def receive_message(self, signature, message):
    #     self._queue.put((signature, message))

    def process_message(self, signature, msg):

        if signature != "robot.command":
            return

        message = copy.deepcopy(msg)

        try:
            com = message["data"]["payload"]["com"]
        except (KeyError, TypeError):
            # если структура не та — просто прокинуть дальше
            self.send_message("robot.command", message)
            return

        # -------------------------
        # VIDEO RECORD
        # -------------------------
        if com == "video_start_record":
            print(10)
            self.send_message(
                "video.record",
                {
                    "record": "start"
                }
            )
            return

        elif com == "video_stop_record":
            self.send_message(
                "video.record",
                {
                    "record": "stop"
                }
            )
            return

        # -------------------------
        # VIDEO PLAY
        # -------------------------
        elif com == "video_start_play":
            self.send_message(
                "video.play",
                {
                    "play": "start"
                }
            )
            return

        elif com == "video_stop_play":
            self.send_message(
                "video.play",
                {
                    "play": "stop"
                }
            )
            return

        elif com == "auto_run":
            self.send_message(
                "robot.control",
                {
                    "control": "start"
                }
            )
            return

        elif com == "auto_stop":
            self.send_message(
                "robot.control",
                {
                    "control": "stop"
                }
            )
            return

        # -------------------------
        # DEFAULT → прокидываем как есть
        # -------------------------
        else:
            self.send_message("robot.command", message)