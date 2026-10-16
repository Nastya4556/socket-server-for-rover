from src.modules.base.base_module.base_module import BaseModule
from src.modules.base.decorator.decorator import *
import pygame



@infinite_loop(0.02)
class JoystickControllerModule(BaseModule):
    ready_for_interface = True
    accepts_any_input = True

    @classmethod
    def config_schema(cls):
        return dict()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pygame.init()
        pygame.joystick.init()
        if pygame.joystick.get_count() == 0:
            raise IOError("Джойстик не найден")
        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()


        self.output_messages = [
            "joystick.command"
        ]


    def main_loop(self):
        pygame.event.pump()
        message = {
            "Ось 1": f"{self.joystick.get_axis(1)}",
            "Ось 3": f"{self.joystick.get_axis(3)}",
            "Ось 6": f"{self.joystick.get_axis(6)}"
            }

        self.send_message("joystick.command", message)

    def process_message(self, signature, message):
        pass