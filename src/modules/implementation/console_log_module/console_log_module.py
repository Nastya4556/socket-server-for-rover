import datetime
from src.modules.base.base_module.base_module import BaseModule

class ConsoleLogModule(BaseModule):

    ready_for_interface = True
    accepts_any_input = True

    @classmethod
    def config_schema(cls):
        return dict()

    def process_message(self, signature, message):
        print(f">>> |LOG {self.name}|{datetime.datetime.now().strftime('%X')}|"
              f"received \"{signature}\", "
              f"contents: {message}")