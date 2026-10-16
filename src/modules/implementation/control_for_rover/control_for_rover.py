from src.modules.base.base_module.base_module import BaseModule
from src.modules.base.decorator.decorator import *

import numpy as np
import csv
import os
from datetime import datetime
import time
from pathlib import Path
import math
import json

@infinite_loop(0.02)
class ControlForRoverModule(BaseModule):
    ready_for_interface = True
    accepts_any_input = True

    @classmethod
    def config_schema(cls):
        return dict()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._min_v_car = 0.00001
        self._car_wheels_state_path = Path(__file__).resolve().parent / "car_wheels_state.json"

        self._critical_angular_acceleration = 0.6
        self._eps_for_acceleration_difference = 0.8

        self._prev_angle_rads = [None, None, None, None]
        self._prev_unwrapped = [None, None, None, None]

        self._offset = [0.0, 0.0, 0.0, 0.0]

        self._to_sid = None
        self._author = None

        self._ticks_lifted = [0, 0, 0, 0]
        self._ticks_for_check_hanging = [0, 0, 0, 0]
        self._ticks_lifted_threshold = 100
        self._ticks_for_check_hanging_threshold = 3

        self._ticks_for_check_grounded = 0
        self._step_for_momentum = 20

        self._prev_momentum_deltas = [None, None, None, None]

        self._message_from_joystick = None

        self._prev_button = None

        self._is_system_work = False#изначально просто езда, алгоритм отключен

        self._prev_gas = 1500

        self._telemetry_dir = "test/telemetry_from_rover_from_trip"
        os.makedirs(self._telemetry_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._telemetry_file = os.path.join(self._telemetry_dir, f"telemetry_{timestamp}.csv")
        self._telemetry_headers_written = False

        self.process_message_functions["joystick.command"] = self.process_message_from_joystick
        self.process_message_functions["data_from_client"] = self.process_message_from_client
        self.process_message_functions["robot.telemetry"] = self.process_message_robot_telemetry

        self.output_messages = [
            "robot.command"
        ]

    def _write_car_wheels_state(self, forward_left_wheel_momentum, forward_right_wheel_momentum,
                                rear_left_wheel_momentum, rear_right_wheel_momentum,
                                forward_left_wheel_angular_velocity, forward_right_wheel_angular_velocity,
                                rear_left_wheel_angular_velocity, rear_right_wheel_angular_velocity):
        data_to_send = {
            "forward_left_wheel_momentum": round(forward_left_wheel_momentum, 6),
            "forward_right_wheel_momentum": round(forward_right_wheel_momentum, 6),
            "rear_left_wheel_momentum": round(rear_left_wheel_momentum, 6),
            "rear_right_wheel_momentum": round(rear_right_wheel_momentum, 6),
            "forward_left_wheel_angular_velocity": round(forward_left_wheel_angular_velocity, 6),
            "forward_right_wheel_angular_velocity": round(forward_right_wheel_angular_velocity, 6),
            "rear_left_wheel_angular_velocity": round(rear_left_wheel_angular_velocity, 6),
            "rear_right_wheel_angular_velocity": round(rear_right_wheel_angular_velocity, 6)
        }
        try:
            self._car_wheels_state_path.write_text(
                json.dumps(data_to_send, ensure_ascii=False),
                encoding = "utf-8"
            )
        except Exception as e:
            pass

    def _parse_wheels(self, message):
        buf = []
        wheels = ["TL", "TR", "BL", "BR"]
        for wheel in wheels:
            motor_data = message.get("motor_" + wheel)
            PIDPos = motor_data.get("PIDPos")
            buf.append(int(PIDPos))

        return buf

    def process_message_from_client(self, message):
        self._to_sid = message.get("to_sid", None)
        self._author = message.get("author", None)

    def process_message_robot_telemetry(self, message):
        telem = message["telemetry"]

        # print(f"telemetry: {telem}")
        # print(f"message from client: {self._to_sid, self._author}")

        if self._message_from_joystick is None:
            return

        current_gas = int(1500 + float(self._message_from_joystick["Ось 1"]) * 500)
        current_turning = int(1500 + float(self._message_from_joystick["Ось 3"]) * 500)

        current_button = (self._message_from_joystick["Ось 6"])

        if float(current_button) < 0.05:
            self._is_system_work = False
        elif float(current_button) > 0.05:
            self._is_system_work = True
        # if self._prev_button is None:
        #     self._prev_button = current_button
        # elif self._prev_button is not None:
        #     if self._prev_button != current_button:
        #         if self._is_system_work == True:
        #             self._is_system_work = False
        #         elif self._is_system_work == False:
        #             self._is_system_work = True
        #         self._prev_button = current_button


        #hanging

        PIDPos = self._parse_wheels(telem)

        grounded = []
        lifted = []

        angle_rads = []

        deltas = []

        for i in range(len(PIDPos)):
            angle_rad = np.deg2rad(PIDPos[i])

            if self._prev_angle_rads[i] is None:
                self._prev_angle_rads[i] = angle_rad
                self._prev_unwrapped[i] = angle_rad
                angle_rads.append(angle_rad)
                deltas.append(0.0)
                continue

            diff = angle_rad - self._prev_angle_rads[i]

            if diff > np.pi:
                self._offset[i] -= 2 * np.pi
            elif diff < -np.pi:
                self._offset[i] += 2 * np.pi

            unwrapped = angle_rad + self._offset[i]
            angle_rads.append(unwrapped)

            # Изменение угла — unwrapped - unwrapped
            delta = unwrapped - self._prev_unwrapped[i]
            deltas.append(delta)

            self._prev_angle_rads[i] = angle_rad
            self._prev_unwrapped[i] = unwrapped

        # if len(deltas) > 0:
        #     positive = [a for a in deltas if a > 0]
        #
        #     if positive:
        #         car_velocity = min(positive)
        #     else:
        #         car_velocity = self._min_v_car
        # else:
        #     car_velocity = self._min_v_car


        # 1 вариант
        abs_deltas = [abs(d) for d in deltas]
        car_velocity = min(abs_deltas)

        #2 вариант
        # held = [i for i in range(4) if self._is_system_work and self._ticks_lifted[i] > 0]
        # free = [abs(deltas[i]) for i in range(4) if i not in held]
        # car_velocity = min(free) if free else self._min_v_car

        for i in range(len(deltas)):
            # 2 вариант
            # if i in held:
            #     lifted.append(i)

            if abs(abs(deltas[i]) - car_velocity) > self._eps_for_acceleration_difference:# и может доавить что скорость колеса больше определенной
                lifted.append(i)
            else:
                grounded.append(i)

        # ----------------------------алгоритм--------------------------------------
        if self._is_system_work:
            print("system work")
            momentum = []
            for i in range(len(self._prev_momentum_deltas)):
                if self._prev_momentum_deltas[i] is not None:
                    momentum.append(self._prev_momentum_deltas[i] + current_gas)
                else:
                    momentum.append(current_gas)

            sum_momentum = np.clip(4 * abs(current_gas - 1500), 0, 2000)

            returned = []

            for i in lifted:
                momentum[i] = 1500
                self._ticks_lifted[i] += 1

                if self._ticks_lifted[i] >= self._ticks_lifted_threshold:
                    momentum[i] = current_gas
                    self._ticks_for_check_hanging[i] += 1

                    if self._ticks_for_check_hanging[i] >= self._ticks_for_check_hanging_threshold:
                        if abs(deltas[i]) < self._critical_angular_acceleration and abs(abs(deltas[i]) - car_velocity) < self._eps_for_acceleration_difference:
                            returned.append(i)

                        self._ticks_lifted[i] = 0
                        self._ticks_for_check_hanging[i] = 0


            for i in returned:
                lifted.remove(i)
                grounded.append(i)

            for i in grounded:
                self._ticks_lifted[i] = 0
                self._ticks_for_check_hanging[i] = 0

            start_momentum = momentum.copy()
            if (len(lifted) == 2 and len(grounded) == 2) or (len(lifted) == 1 and len(grounded) == 3):
                for i in grounded:
                    if current_gas >= 1500:
                        momentum[i] += self._step_for_momentum
                    else:
                        momentum[i] -= self._step_for_momentum
                    momentum[i] = int(np.clip(momentum[i], 1000, 2000))

                    # суммарное усилие = отклонения ВСЕХ колёс от нейтрали
                    buf_momentum = sum(abs(m - 1500) for m in momentum)
                    if buf_momentum > sum_momentum:
                        for j in grounded:
                            momentum[j] = start_momentum[j]


            if len(lifted) == 0:
                momentum = [current_gas, current_gas, current_gas, current_gas]
                self._prev_momentum_deltas = [0, 0, 0, 0]

            elif len(lifted) != 0:
                for i in range(len(momentum)):
                    self._prev_momentum_deltas[i] = momentum[i] - current_gas

            if (self._prev_gas > 1500 and current_gas <= 1500) or (self._prev_gas < 1500 and current_gas >= 1500):
                for i in range(len(momentum)):
                    self._prev_momentum_deltas[i] = 0
                    momentum[i] = current_gas

            self._prev_gas = current_gas
            momentum = [int(np.clip(momentum[0], 1000, 2000)), int(np.clip(momentum[1], 1000, 2000)), int(np.clip(momentum[2], 1000, 2000)), int(np.clip(momentum[3], 1000, 2000))]
        elif self._is_system_work == False:
            print("system don't work")
            value = int(np.clip(current_gas, 1200, 1800))
            momentum = [value, value, value, value]
            self._prev_momentum_deltas = [None] * 4
            self._ticks_lifted = [0] * 4
            self._ticks_for_check_hanging = [0] * 4
            self._prev_gas = current_gas

        #------------------------------------------------------------------
        # print(buf)
        all_current = 400
        buf = f'{{"all_current": {all_current},"tl": {momentum[0]}, "tr": {momentum[1]}, "bl":{momentum[2]},  "br": {momentum[3]}, "st": {current_turning}}}'
        message = {"com": buf}
        print(buf)

        self._write_car_wheels_state(momentum[0], momentum[1],
                                    momentum[2], momentum[3],
                                    deltas[0], deltas[1],
                                    deltas[2], deltas[3])

        self.send_message(
            "robot.command",
            {
                "to_sid": self._to_sid,
                "data": {
                    "payload": message, "author": self._author
                },
            }
        )
        if len(deltas) == 4 and len(momentum) == 4 and telem is not None:
            row = {
                "time_stm": telem.get("time_stm"),
                "time_nano": telem.get("time_nano"),
                "current_gas": current_gas,
                "current_turning": current_turning,
                "delta_tl": deltas[0],
                "delta_tr": deltas[1],
                "delta_bl": deltas[2],
                "delta_br": deltas[3],
                "momentum_tl": momentum[0],
                "momentum_tr": momentum[1],
                "momentum_bl": momentum[2],
                "momentum_br": momentum[3],
                "all_current": all_current,
            }
            nested_keys = [
                "motor_TL", "motor_TR", "motor_BL", "motor_BR",
                "servo_T", "servo_B",
                "sensors_T", "sensors_B",
                "controller",
                "fet",
            ]
            for section in nested_keys:
                data = telem.get(section, {})
                for key, val in data.items():
                    row[f"{section}__{key}"] = val

            with open(self._telemetry_file, "a", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=row.keys(), extrasaction='ignore')
                if not self._telemetry_headers_written:
                    writer.writeheader()
                    self._telemetry_headers_written = True
                writer.writerow(row)



    def process_message_from_joystick(self, message):
        self._message_from_joystick = message
