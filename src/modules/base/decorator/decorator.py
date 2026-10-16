import threading
import asyncio
import websockets, websocket
import json
import secrets
import uuid



#main_loop выполняется бесконечно с заданным интервалом
#задает целевой функцей потока run_loop
def infinite_loop(t):
    def loop_decorator(cls):
        class NewClass(cls):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self._loop_timer = t

            def _receive_message(self, signature, message):
                data = signature, message
                self._queue.put(data)
                with self._cond_var:
                    self._cond_var.notify()

            def _run_loop(self):
                while getattr(self, "_running", True):
                    with self._cond_var:
                        if not self._queue.empty():
                            data = self._queue.get()
                            self.process_message(data[0], data[1])
                            continue

                        self.main_loop()
                        self._cond_var.wait(self._loop_timer)

        NewClass.__name__ = cls.__name__
        NewClass.__qualname__ = cls.__qualname__

        return NewClass
    return loop_decorator


def websocket_server(cls):
    class NewClass(cls):
        def __init__(self, *args, **kwargs):
            self.host = kwargs.pop('host', 'localhost')
            self.port = kwargs.pop('port', 7000)
            self._connected = {}
            self._ws_event = None
            super().__init__(*args, **kwargs)

            if not hasattr(self, '_loop_timer'):
                self._loop_timer = 1


        def _validation(self, token):
            return True

        async def _handshake(self, websocket):
            print('Starting handshake')
            handshake_json = await websocket.recv()
            handshake_data = json.loads(handshake_json)

            if handshake_data['token']:
                archive_token = handshake_data['token']
                print(f'archive token: {archive_token}')
            else:
                archive_token = None
                print('no archive token')

            # протокол соединения
            if handshake_data['protocol'] == "anonymous.v1":
                print('Protocol: anonymous.v1')
            elif handshake_data['protocol'] == "auth.v1":
                print('Protocol: auth.v1')
                # обработка старого токена
                if archive_token:
                    valid = self._validation(handshake_data['token'])
                    if not valid:
                        print("Invalid token. Closing connection.")
                        await websocket.send("Invalid token. Closing connection.")
                        await websocket.close()
                else:
                    print("No token to auth. Closing connection.")
                    await websocket.send("No token to auth. Closing connection.")
                    await websocket.close()

            else:
                print("Invalid protocol. Closing connection.")
                await websocket.send("Invalid protocol. Closing connection.")
                await websocket.close()

            id = str(uuid.uuid4())
            print(f'id: {id}')

            token = secrets.token_urlsafe()
            print(f'assigned token: {token}')
            connection = {
                    "id": id,
                    "ws": websocket,
                    "token": token,
                    "name": handshake_data["name"],
                    "protocol": handshake_data["protocol"]
            }
            self._connected[id] = connection

            connection_data = {"connection_data": {
                    "id": id,
                    "token": token,
                    "name": handshake_data["name"],
                    "protocol": handshake_data["protocol"]
            }}
            await websocket.send(json.dumps(connection_data))

            print("Handshake complete")

            return connection

        async def _handler(self, websocket):
            connection = None
            try:
                connection = await self._handshake(websocket)
                async for message in websocket:
                    self._receive_websocket(message)
            except websockets.ConnectionClosed:
                pass
            except Exception as e:
                print(f"[ERROR] handler error: {e}")
            finally:
                if connection:
                    self._connected.pop(connection['id'], None)

        async def _send_websocket_all_async(self, message):
            for connection in list(self._connected.values()):  # ← копия словаря
                try:
                    await connection['ws'].send(message)
                except Exception:
                    pass

        def send_websocket_all(self, message):
            asyncio.create_task(self._send_websocket_all_async(message))

        async def _send_websocket_async(self, id, message):
            connection = self._connected[id]['ws']
            await connection.send(message)

        def send_websocket(self, id, message):
            asyncio.create_task(self._send_websocket_async(id, message))

        def _receive_websocket(self, message):
            self.process_websocket(message)

        async def _ws_loop(self):
            self._server = await websockets.serve(self._handler, self.host, self.port)
            await asyncio.Future()

        async def main_loop_async(self):
            while True:
                self.main_loop()
                await asyncio.sleep(self._loop_timer)

        def _run_loop(self):
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            self._loop = new_loop
            self._ws_event = asyncio.Event()

            ws_task = new_loop.create_task(self._ws_loop())
            main_task = new_loop.create_task(self.main_loop_async())

            new_loop.run_until_complete(asyncio.gather(ws_task, main_task))

    NewClass.__name__ = cls.__name__
    NewClass.__qualname__ = cls.__qualname__
    return NewClass



# Заменить существующий websocket_client на этот код (вместо старого NewClass)
def websocket_client(cls):
    import threading
    class NewClass(cls):
        def __init__(self, *args, **kwargs):
            # параметры подключения
            self.host = kwargs.pop('host', 'localhost')
            self.port = kwargs.pop('port', 7000)
            self.protocol = kwargs.pop('protocol', "anonymous.v1")
            self.ping_interval = kwargs.pop('ping_interval', 0.2)
            super().__init__(*args, **kwargs)

            self._thread = threading.Thread(target=self._run_loops_async, daemon=True)
            self.connected = False
            self._ws_thread = None

            def on_message(ws, message):
                msg = json.loads(message)
                if "connection_data" in msg:
                    self.connection_data = msg["connection_data"]
                    self.connected = True
                else:
                    self.process_websocket(message)

            def on_open(ws):
                print("Client: Connection successful")
                self.connection_data = {
                    "name": self.name,
                    "token": "123",
                    "protocol": self.protocol
                }
                # self.connected = True
                ws.send(json.dumps(self.connection_data))

            def on_disconnect(self):
                pass

            def on_close(wsapp, close_status_code, close_msg):
                self.connected = False
                self.on_disconnect()
                print("[WS] connection closed")


            def on_error(ws, error):
                self.connected = False
                print(f"[WS] connection error: {error}")

            self.ws = websocket.WebSocketApp(
                f"ws://{self.host}:{self.port}",
                on_open=on_open,
                on_message=on_message,
                on_close=on_close,
                on_error=on_error
            )

        async def main_loop_async(self):
            # дождаться подключения перед запуском основного loop, но ограниченно
            wait_count = 0
            while not self.connected and wait_count < 10:
                await asyncio.sleep(0.2)
                wait_count += 1
            # теперь запускаем основную loop (sync main_loop)
            self._run_loop()

        def _start_ws_thread(self):
            if self._ws_thread and self._ws_thread.is_alive():
                return
            self._ws_thread = threading.Thread(
                target=lambda: self.ws.run_forever(
                    ping_interval=self.ping_interval,
                    reconnect=3  # пересоединяться каждые 3 секунды после разрыва
                ),
                daemon=True
            )
            self._ws_thread.start()

        async def ws_loop(self):
            # просто триггер старта потокового WS — не используем run_in_executor
            await asyncio.get_running_loop().run_in_executor(None, lambda: None)
            # Ничего не ждём здесь, WebSocket работает в собственном потоке

        def _run_loops_async(self):
            # здесь создаём свой event loop для main_loop_async, но WS в отдельном thread
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)

            # стартуем WS-нить до запуска асинхронных задач, чтобы handshake прошёл рано
            self._start_ws_thread()

            # планируем задачи: main_loop_async только
            main_task = new_loop.create_task(self.main_loop_async())

            try:
                new_loop.run_until_complete(main_task)
            except Exception as e:
                print(f"[ERROR] _run_loops_async loop crashed: {e}")
            finally:
                try:
                    new_loop.close()
                except Exception:
                    pass

        def _run_thread(self):
            self._thread.start()

        def send_websocket(self, message):
            try:
                if self.ws and self.connected:
                    self.ws.send(message)
                else:
                    print("[WARN] trying to send while websocket not connected")
            except Exception as e:
                print(f"[ERROR] send_websocket failed: {e}")


    NewClass.__name__ = cls.__name__
    NewClass.__qualname__ = cls.__qualname__
    return NewClass

