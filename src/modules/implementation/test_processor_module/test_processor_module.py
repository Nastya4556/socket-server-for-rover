import time
from src.modules.base.base_module.base_module import BaseModule


class ProcessorModule(BaseModule):
    def process_message(self, signature, message):
        data = f"{message['name']} - position: x:{message['position']['x']}, y:{message['position']['y']}"
        self.send_message("processed_car_data", data)