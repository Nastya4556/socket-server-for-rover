import socket
import time
from src.modules.base.decorator.decorator import *
from src.modules.base.base_module.base_module import BaseModule
import random
import queue
#
#
# {
#     "RemoteController": {
#         "wheels": [{
#             "steeringAngle": 0,
#             "Drive Torque": 0
#         }]
#
#     }
# }
#
#
# {"CarStats":
#      {"engineRotationSpeed":600.00006103515625,
#       "linearVelocity":{"x":0,"y":0,"z":0},
#       "angularVelocity":{"x":0,"y":0,"z":0},
#       "selectedGear":0,
#       "getForwardSpeed":0,
#       "wheels":[{"inContact":true,"contantPoint":{"x":-387.403876609902,"y":1502.1107782150136,"z":-6.6899139581094254},
#                  "physMaterial":"DefaultPhysicalMaterial",
#                  "normalizedSuspensionLenght":0.14837156236171722,
#                  "springForce":300029.125,
#                  "slipAngle":1.5431604385375977,
#                  "isSlipping":false,
#                  "slipMagnitude":0,
#                  "isSkidding":false,
#                  "skidMagnitude":-0.10833814740180969,
#                  "skidNormal":{"x":0,"y":0,"z":0},
#                  "suspensionOffset":1.9257349967956543,"wheelRotationAngle":-0.52327537536621094,"steeringAngle":0,"wheelAngularVelocity":8.3188482676632702e-05},
#                 {"inContact":true,"contantPoint":{"x":-388.94987482697707,"y":1649.5700818241796,"z":-0.90579570563954803},"physMaterial":"DefaultPhysicalMaterial","normalizedSuspensionLenght":0.084728516638278961,"springForce":319141.21875,"slipAngle":1.5433515310287476,"isSlipping":false,"slipMagnitude":0,"isSkidding":false,"skidMagnitude":-0.10833814740180969,"skidNormal":{"x":0,"y":0,"z":0},"suspensionOffset":2.8047914505004883,"wheelRotationAngle":-3.8869678974151611,"steeringAngle":0,"wheelAngularVelocity":8.2613143604248762e-05},
#                 {"inContact":true,"contantPoint":{"x":-633.15369051641028,"y":1499.6781492351672,"z":-10.377348433156065},"physMaterial":"DefaultPhysicalMaterial","normalizedSuspensionLenght":0.40857315063476562,"springForce":297115.25,"slipAngle":1.5431690216064453,"isSlipping":false,"slipMagnitude":0,"isSkidding":false,"skidMagnitude":-0.10837304592132568,"skidNormal":{"x":0,"y":0,"z":0},"suspensionOffset":1.8285170793533325,"wheelRotationAngle":-0.49291995167732239,"steeringAngle":0,"wheelAngularVelocity":8.3189625001978129e-05},{"inContact":true,"contantPoint":{"x":-634.66583917307889,"y":1647.2174479637365,"z":-6.9937894311200992},"physMaterial":"DefaultPhysicalMaterial","normalizedSuspensionLenght":0.48413047194480896,"springForce":256088.25,"slipAngle":1.5433598756790161,"isSlipping":false,"slipMagnitude":0,"isSkidding":false,"skidMagnitude":-0.10837312787771225,"skidNormal":{"x":0,"y":0,"z":0},"suspensionOffset":0.30542808771133423,"wheelRotationAngle":-3.8865823745727539,"steeringAngle":0,"wheelAngularVelocity":8.2614540588110685e-05}]}}




@infinite_loop(1)
class UnrealCarModule(BaseModule):

    ready_for_interface = True

    @classmethod
    def config_schema(cls):
        return {
            "host": "str",
            "port": "int"
        }

    def __init__(self, *args, host="127.0.0.1", port=8001, **kwargs):
        super().__init__(*args, **kwargs)
        self.host = host
        self.port = int(port)
        self.backlog = 5
        self.accept_timeout = 0.1
        self.recv_timeout = 1.0
        self.reconnect_delay = 1.0

        # хранение подключений роботов: addr -> info
        self.robots = {}
        self.robots_lock = threading.Lock()

        # флаг для остановки сервера
        self.stop_event = threading.Event()

        self.process_message_functions["robot.command"] = self.process_message_robot_command
        self.process_message_functions["raw_ue_data"] = self.process_message_ue_data


        # поток серверного слушателя
        self.thread = threading.Thread(target=self.server_worker, daemon=True)
        self.thread.start()

#     def main_loop(self):
#         command = {
#                   "AssistStats": {
#                     "assistWheel_FR": {
#                       "drive": 0,
#                       "break": 1,
#                       "handBreak": True
#                     },
#                     "assistWheel_FL": {
#                       "drive": 0,
#                       "break": 1,
#                       "handBreak": True
#                     },
#                     "assistWheel_RR": {
#                       "drive": 0,
#                       "break": 1,
#                       "handBreak": True
#                     },
#                     "assistWheel_RL": {
#                       "drive": 0,
#                       "break": 1,
#                       "handBreak": True
#                     }
#                   }
# }
#
#         payload = json.dumps(command)
#         # положить в send_q каждого робота
#         with self.robots_lock:
#             for addr, info in list(self.robots.items()):
#                 try:
#                     info['send_q'].put(payload)
#                 except Exception:
#                     pass

    # def process_message(self, signature, message):
    #     try:
    #         payload = json.loads(message)
    #         if "CarStats" in payload:
    #             self.send_message("raw_ue_data", payload)
    #             return
    #
    #     except (json.JSONDecodeError, TypeError) as e:
    #         print(f"[WARN] process_message: failed to parse message: {e}")

    def process_message_ue_data(self, message):
        try:
            payload = json.loads(message)
            if "CarStats" in payload:
                self.send_message("raw_ue_data", payload)
                return

        except (json.JSONDecodeError, TypeError) as e:
            print(f"[WARN] process_message: failed to parse message: {e}")


    def process_message_robot_command(self, message):
        payload = json.dumps(message)
        with self.robots_lock:
            for addr, info in list(self.robots.items()):
                try:
                    info['send_q'].put(payload)
                except Exception:
                    pass





    def server_worker(self):
        srv = None
        try:
            srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind((self.host, self.port))
            srv.listen(self.backlog)
            srv.settimeout(self.accept_timeout)
        except Exception:
            # не удалось поднять сервер — выйдем
            try:
                if srv:
                    srv.close()
            except Exception:
                pass
            return

        while not self.stop_event.is_set():
            try:
                try:
                    client_sock, addr = srv.accept()
                except socket.timeout:
                    continue

                client_sock.settimeout(self.recv_timeout)
                send_q = queue.Queue()

                recv_t = threading.Thread(target=self.recv_loop, args=(client_sock, addr), daemon=True)
                send_t = threading.Thread(target=self.send_loop, args=(client_sock, addr, send_q), daemon=True)

                with self.robots_lock:
                    self.robots[addr] = {'sock': client_sock, 'send_q': send_q, 'recv_thread': recv_t, 'send_thread': send_t}

                recv_t.start()
                send_t.start()

                # не блокируем accept: просто продолжаем принимать новые соединения
            except Exception:
                # на ошибки в accept/создании потоков — подождать и продолжить
                time.sleep(self.reconnect_delay)
                continue

        try:
            srv.close()
        except Exception:
            pass

    def recv_loop(self, sock, addr):
        while not self.stop_event.is_set():
            try:
                chunk = sock.recv(4096)
            except socket.timeout:
                continue
            except Exception:
                break
            if not chunk:
                break
            # chunk — bytes; публикуем как есть
            with self._cond_var:
                self._queue.put(("raw_ue_data", chunk.decode('utf-8', errors='replace')))
                self._cond_var.notify()
        # соединение закрыто
        with self.robots_lock:
            try:
                info = self.robots.pop(addr, None)
            except Exception:
                info = None
        try:
            sock.close()
        except Exception:
            pass

    def send_loop(self, sock, addr, send_q):
        while not self.stop_event.is_set():
            try:
                item = send_q.get(timeout=0.5)
            except queue.Empty:
                continue
            if item is None:
                continue
            try:
                if isinstance(item, (bytes, bytearray)):
                    data = bytes(item)
                elif isinstance(item, str):
                    data = item.encode("utf-8")
                else:
                    data = str(item).encode("utf-8")
                sock.sendall(data)
            except Exception:
                # при ошибке — вернуть сообщение в очередь (попытка повторить) и выйти
                try:
                    send_q.put(item)
                except Exception:
                    pass
                break
        try:
            sock.close()
        except Exception:
            pass
        with self.robots_lock:
            try:
                self.robots.pop(addr, None)
            except Exception:
                pass

    def stop(self):
        self.stop_event.set()
        with self._cond_var:
            try:
                self._cond_var.notify_all()
            except Exception:
                pass
        # закрыть все клиентские сокеты
        with self.robots_lock:
            for addr, info in list(self.robots.items()):
                try:
                    info['send_q'].put(None)
                except Exception:
                    pass
                try:
                    info['sock'].shutdown(socket.SHUT_RDWR)
                except Exception:
                    pass
                try:
                    info['sock'].close()
                except Exception:
                    pass
            self.robots.clear()
