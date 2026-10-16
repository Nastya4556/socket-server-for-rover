from src.modules.base.decorator.decorator import *
from src.modules.base.base_module.base_module import BaseModule

@infinite_loop(1)
class SenderModule(BaseModule):
    def __init__(self, signature, message, *args, **kwargs, ):
        super().__init__(*args, **kwargs)
        self.signature = signature
        self.message = message

    def main_loop(self):
        self.send_message(self.signature, self.message)