import threading
import queue


class BaseModule:

    ready_for_interface = False
    accepts_any_input = False

    @classmethod
    def config_schema(cls):
        return dict()

    def __init__(self, name, manager, receivers=None, senders=None):
        self.name = name
        self._manager = manager
        self._manager.add_module(self)
        self._receivers = dict() if receivers is None else receivers
        self._senders = dict() if senders is None else senders

        self.process_message_functions = dict()
        self.output_messages = []

        self._thread = threading.Thread(target=self._run_loop)
        self._queue = queue.Queue()
        self._cond_var = threading.Condition()
        self._running = False

    def start_thread(self):
        if self._thread:
            if not self._thread.is_alive():
                self._running = True
                self._thread.start()

    def _receive_message(self, signature, message):
        data = signature, message
        self._queue.put(data)
        with self._cond_var:
            self._cond_var.notify()

    def _run_loop(self):
        self.main_loop()
        while self._running:
            with self._cond_var:
                if not self._queue.empty():
                    data = self._queue.get()
                    self.process_message(data[0], data[1])
                    continue
                else:
                    self._cond_var.wait()


    def _add_sender(self, signature, sender):
        if "modules" in self._senders[signature]:
            self._senders[signature]["modules"].append(sender)
        else:
            self._senders[signature]["modules"] = [sender]

    def _add_receiver(self, signature, receiver):
        if "modules" in self._receivers[signature]:
            self._receivers[signature]["modules"].append(receiver)
        else:
            self._receivers[signature]["modules"] = [receiver]

    def send_message(self, signature, message):
        if signature in self._receivers:
            subs = list(self._receivers[signature]["modules"])
            for subscriber in subs:
                subscriber._receive_message(signature, message)


    def process_message(self, signature, message):
        if signature in self.process_message_functions:
            self.process_message_functions[signature](message)

    def main_loop(self):
        pass

    def stop(self):
        """Останавливает поток и очищает очередь."""
        self._running = False
        with self._cond_var:
            self._cond_var.notify_all()
        if self._thread.is_alive():
            self._thread.join(timeout=1)

        # Очистка входящих и исходящих соединений
        self._receivers.clear()
        self._senders.clear()
        with self._queue.mutex:
            self._queue.queue.clear()
        self.process_message_functions.clear()
        self.output_messages.clear()

    def __del__(self):
        try:
            print(12)
            self.stop()
        except Exception as ex:
            print(ex)