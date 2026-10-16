from src.modules.base.decorator.decorator import *
from src.modules.base.base_module.base_module import BaseModule


@infinite_loop(1)
class CarModule(BaseModule):

    ready_for_interface = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.process_message_functions["car.command"] = self.process_message_command
        self.output_messages = ["raw_car_data"]

        self.pos = {
            "x": 0,
            "y": 0
        }
        self.speed = {
            "x": 0,
            "y": 0
        }
        self.acceleration = {
            "x": -1,
            "y": -1
        }

    def accelerate(self):
        if self.speed["x"] > 0:
            self.speed["x"] = self.speed["x"] + self.acceleration["x"]
        elif self.speed["x"] < 0:
            self.speed["x"] = self.speed["x"] - self.acceleration["x"]
        if self.speed["y"] > 0:
            self.speed["y"] = self.speed["y"] + self.acceleration["y"]
        elif self.speed["y"] < 0:
            self.speed["y"] = self.speed["y"] - self.acceleration["y"]

    def move(self):
        self.pos["x"] += self.speed["x"]
        self.pos["y"] += self.speed["y"]
        self.accelerate()

    def add_speed(self, x, y):
        self.speed["x"] += x
        self.speed["y"] += y

    def print_data(self):
        print(f"{self.name}: position: {self.pos['x']}, {self.pos['y']}",
              f"speed: {self.speed['x']}, {self.speed['y']}",
              f"acceleration: {self.acceleration['x']}, {self.acceleration['y']}")


    def process_message_command(self, message):
        x = message["x"]
        y = message["y"]
        self.add_speed(x, y)

    def main_loop(self):
        self.move()

        data = {
            "name": self.name,
            "position": {
                "x": self.pos["x"],
                "y": self.pos["y"]
            },
            "speed": {
                "x": self.speed["x"],
                "y": self.speed["y"]
            },
            "acceleration": {
                "x": self.acceleration["x"],
                "y": self.acceleration["y"]
            }
        }

        self.send_message("raw_car_data", data)
        self.move()