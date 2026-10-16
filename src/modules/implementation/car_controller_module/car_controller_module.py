from src.modules.base.decorator.decorator import *
from src.modules.base.base_module.base_module import BaseModule

@infinite_loop(1)
class CarControllerModule(BaseModule):

    ready_for_interface = True

    @classmethod
    def config_schema(cls):
        return {
            "x": "int",
            "y": "int",
        }

    def __init__(self, x=0, y=0, *args, **kwargs,):
        super().__init__(*args, **kwargs)
        self.x = x
        self.y = y

        self.output_messages = ["car.command"]

    def main_loop(self):
        command = {
            "x": self.x,
            "y": self.y
        }
        self.send_message("car.command", command)