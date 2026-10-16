import threading

from .web_manager import WebManagerInterface
from .utils import discover_modules


class ManagerModule:

    def __init__(
        self,
        web_interface=False,
        host="0.0.0.0",
        port=8001
    ):

        self.modules = dict()
        self.connections = list()

        self.web_interface = web_interface
        self.web_modules = dict()

        self.host = host
        self.port = port

        self._load_modules()

        # веб интерфейс
        if self.web_interface:
            self.web = WebManagerInterface(self)
            self.app = self.web.app
            self._start_web_server()
        else:
            self.web = None
            self.app = None



    # ------------------------------------------------
    # web interface
    # ------------------------------------------------

    def _start_web_server(self):

        import uvicorn

        def run():
            uvicorn.run(
                self.app,
                host=self.host,
                port=self.port,
                log_level="info"
            )

        self._web_thread = threading.Thread(target=run, daemon=True)
        self._web_thread.start()

    # ------------------------------------------------
    # discover modules
    # ------------------------------------------------

    def _load_modules(self):

        import src.modules.implementation as implementation
        self.web_modules = discover_modules(implementation)


    def get_available_modules(self):

        result = {}
        for name, cls in self.web_modules.items():
            inputs = []
            outputs = []

            if hasattr(cls, "config_schema"):
                config = cls.config_schema()
            else:
                config = {}

            result[name] = {
                "type": name,
                "config": config
            }
        return result


    # ------------------------------------------------
    # manage modules
    # ------------------------------------------------


    def add_module(self, module):

        self.modules[module.name] = module


    def create_module(self, module_type, name, *args, **kwargs):

        if module_type not in self.web_modules:
            raise ValueError(f"Uncompatible with web-type module type {module_type}")

        if name in self.modules:
            raise ValueError(f"Module {name} already exists")

        cls = self.web_modules[module_type]
        module = cls(
            name=name,
            manager=self,
            *args,
            **kwargs
        )
        self.modules[name] = module

        return module


    def delete_module(self, name):

        if name not in self.modules:
            return False

        self.modules[name].stop()

        # удалить соединения
        self.connections = [
            c for c in self.connections
            if c["sender"] != name and c["receiver"] != name
        ]

        del self.modules[name]

        return True


    def get_modules(self):
        result = {}

        for name, module in self.modules.items():

            inputs = list(module.process_message_functions.keys())

            outputs = module.output_messages

            result[name] = {
                "name": name,
                "type": module.__class__.__name__,
                "inputs": inputs,
                "outputs": outputs,
                "accepts_any_input": getattr(module, "accepts_any_input", False),
                "running": getattr(module, "_running", False)
            }

        return result


    # ------------------------------------------------
    # manage connections
    # ------------------------------------------------

    def connect(self, sender_name, receiver_name, signature):

        if sender_name not in self.modules:
            raise ValueError("Sender not found")

        if receiver_name not in self.modules:
            raise ValueError("Receiver not found")

        sender = self.modules[sender_name]
        receiver = self.modules[receiver_name]

        # проверка сигнатуры
        if signature not in sender.output_messages:
            raise ValueError("Sender does not emit this signal")

        connection = {
            "sender": sender_name,
            "receiver": receiver_name,
            "signature": signature
        }

        if connection in self.connections:
            return False

        self.connections.append(connection)

        # обновить runtime связь
        if signature not in sender._receivers:
            sender._receivers[signature] = {"modules": []}

        sender._add_receiver(signature, receiver)

        return True


    def disconnect(self, sender_name, receiver_name, signature):

        sender = self.modules.get(sender_name)
        receiver = self.modules.get(receiver_name)

        if not sender or not receiver:
            return False

        self.connections = [
            c for c in self.connections
            if not (
                c["sender"] == sender_name and
                c["receiver"] == receiver_name and
                c["signature"] == signature
            )
        ]

        if signature in sender._receivers:

            sender._receivers[signature]["modules"] = [
                m for m in sender._receivers[signature]["modules"]
                if m.name != receiver_name
            ]

        return True

    def connect_all_modules(self):
        for module_name, module in self.modules.items():
            for signature_name, signature_data in module._receivers.items():
                for receiver_module_name in signature_data["names"]:
                    module._add_receiver(signature_name, self.modules[receiver_module_name])



    def get_connections(self):

        return self.connections


    # ------------------------------------------------
    # graph
    # ------------------------------------------------

    def get_graph(self):

        nodes = []
        edges = []

        for name, module in self.modules.items():

            nodes.append({
                "id": name,
                "type": module.__class__.__name__,
                "inputs": list(module.process_message_functions.keys()),
                "outputs": module.output_messages,
                "accepts_any_input": getattr(module, "accepts_any_input", False),
                "running": getattr(module, "_running", False)
            })

        for c in self.connections:

            edges.append({
                "from": c["sender"],
                "to": c["receiver"],
                "signal": c["signature"]
            })

        return {
            "nodes": nodes,
            "edges": edges
        }


    # ------------------------------------------------
    # threads
    # ------------------------------------------------

    def start_module(self, name):

        if name not in self.modules:
            return False

        self.modules[name].start_thread()

        return True


    def start_all_threads(self):

        for module in self.modules.values():
            module.start_thread()



    def print_graph(self):

        print("\nModules:")
        for name in self.modules:
            print(" ", name)

        print("\nConnections:")
        for c in self.connections:
            print(
                f' {c["sender"]} --{c["signature"]}--> {c["receiver"]}'
            )
