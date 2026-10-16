from src.modules.base.base_module.base_module import BaseModule
from src.modules.base.decorator.decorator import *
import numpy as np

import csv
import json
import os
from pathlib import Path


@infinite_loop(1)
class PidControlForAnrealModule(BaseModule):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._params_path = Path(__file__).resolve().parent / "params.json"
        self._car_wheels_state_path = Path(__file__).resolve().parent / "car_wheels_state.json"

        with open(self._params_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self._kp = data['kp']
        self._kd = data['kd']

        self._current_gas = data['gas']

        # self._kp = 50
        # self._kd = 40

        self._prev_velocities = [None, None, None, None]

        self._min_v_car = 0.00001

        self._wheel_radius = 0.36

        self._target_yaw = None

        self._eps_for_yaw_difference = 0.2

        self._prev_yaw_difference = None

        self._step_for_momentum = 25
        self._ticks_lifted = [0, 0, 0, 0]

        self._critical_angular_velocity = 0.1

        self._momentum_deltas = [None, None, None, None]

        self._ticks_lifted_threshold = 8
        self._ticks_for_check_hanging_threshold = 1
        self._ticks_for_check_hanging = [0, 0, 0, 0]

        self._eps_for_velocity_difference = 0.07

        log_dir = "test/telemetry_from_anreal_from_trip"
        os.makedirs(log_dir, exist_ok=True)
        self._log_path = os.path.join(log_dir, "telemetry_log_gas_475.csv")
        file_is_new = (not os.path.exists(self._log_path)) or os.path.getsize(self._log_path) == 0
        self._log_file = open(self._log_path, "a", newline="")
        self._log_writer = csv.writer(self._log_file)
        if file_is_new:
            self._log_writer.writerow([
                "angular_velocity_fl_mps", "angular_velocity_fr_mps", "angular_velocity_rl_mps", "angular_velocity_rr_mps",  # скорость колёс в м/с
                "yaw_difference",
                "initial_momentum",
                "momentum_fl", "momentum_fr", "momentum_rl", "momentum_rr",
            ])
            self._log_file.flush()

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

    def _get_yaw(self, message):
        raw = message.get("CarStats")
        globalRotation = raw.get("globalRotation")
        return globalRotation.get("yaw")

    def _parse_wheels(self, message):
        raw = message.get("CarStats", {}).get("wheels", [])
        return [
            {
                "angular_velocity": wheel.get("wheelAngularVelocity", 0.0),
                "is_in_contact": wheel.get("inContact"),
                "drive_torque": wheel.get("driveTorque")
            }
            for wheel in raw
        ]


    def process_message(self, signature, message):
        if signature != "raw_ue_data":
            return
        wheels = self._parse_wheels(message)

        yaw = self._get_yaw(message)
        if self._target_yaw == None:
            self._target_yaw = yaw

        yaw_difference = ((self._target_yaw - yaw) + 180) % 360 - 180

        angular_velocities = []

        for i, wheel in enumerate(wheels):
            angular_velocities.append(wheel["angular_velocity"] * np.pi / 180 * self._wheel_radius) # теперь скорсоть в м/c

        #определяю скорость машины по минимальной скорости колеса
        if len(angular_velocities) > 0:
            positive_velocities = [abs(velocity) for velocity in angular_velocities]
            if positive_velocities:
                car_velocity = min(positive_velocities)
            else:
                car_velocity = self._min_v_car

        lifted = []
        grounded = []

        for i, wheel in enumerate(wheels):
            if abs(angular_velocities[i]) > self._critical_angular_velocity and abs(angular_velocities[i]) - car_velocity > self._eps_for_velocity_difference:
                lifted.append(i)
            else:
                grounded.append(i)

        current_gas = self._current_gas
        sum_momentum = 4 * current_gas
        momentum = []

        for i in range(len(self._momentum_deltas)):
            if self._momentum_deltas[i] == None or len(lifted) == 0:
                momentum.append(current_gas)
            else:
                momentum.append(current_gas + self._momentum_deltas[i])

        newly_grounded = []
        for i in list(lifted):
            momentum[i] = 0
            self._ticks_lifted[i] += 1
            if self._ticks_lifted[i] >= self._ticks_lifted_threshold:
                momentum[i] = current_gas
                self._ticks_for_check_hanging[i] += 1
                if self._ticks_for_check_hanging[i] >= self._ticks_for_check_hanging_threshold:
                    if abs(angular_velocities[i]) < self._critical_angular_velocity or \
                            abs(car_velocity - angular_velocities[i]) < self._eps_for_velocity_difference:
                        newly_grounded.append(i)
                    self._ticks_lifted[i] = 0
                    self._ticks_for_check_hanging[i] = 0

        for i in newly_grounded:
            grounded.append(i)
            lifted.remove(i)

        current_momentum_buf = list(momentum)
        if (len(lifted) == 2 and len(grounded) == 2) or (len(lifted) == 1 and len(grounded) == 3):
            for i in grounded:
                momentum[i] += self._step_for_momentum
                momentum[i] = np.clip(momentum[i], 0, 1000)

            buf_sum = sum(momentum)
            if buf_sum > sum_momentum:
                for i in grounded:
                    momentum[i] = current_momentum_buf[i]

        if len(lifted) == 0:
            for i in range(len(momentum)):
                momentum[i] = current_gas

        for i in range(len(momentum)):
            self._momentum_deltas[i] = momentum[i] - current_gas

        if self._prev_yaw_difference == None:
            delta_momentum = self._kp * abs(yaw_difference) + self._kd * abs(yaw_difference)

            delta_momentum_for_contact = delta_momentum * (len(grounded) / 4)
        else:
            delta_momentum = self._kp * abs(yaw_difference) + self._kd * abs(yaw_difference - self._prev_yaw_difference)

            delta_momentum_for_contact = delta_momentum * (len(grounded) / 4)

        if abs(yaw_difference) > self._eps_for_yaw_difference and yaw_difference > 0:#у левых прибавляю [0, 2], у правых убавляю [1, 3]
            for i in [0, 2]:
                if i in grounded:
                    momentum[i] = np.clip(momentum[i] + delta_momentum_for_contact, 0, 1000)
            for i in [1, 3]:
                if i in grounded:
                    momentum[i] = np.clip(momentum[i] - delta_momentum_for_contact, 0, 1000)

        elif abs(yaw_difference) > self._eps_for_yaw_difference and yaw_difference < 0:
            for i in [0, 2]:
                if i in grounded:
                    momentum[i] = np.clip(momentum[i] - delta_momentum_for_contact, 0, 1000)
            for i in [1, 3]:
                if i in grounded:
                    momentum[i] = np.clip(momentum[i] + delta_momentum_for_contact, 0, 1000)

        self._prev_yaw_difference = yaw_difference

        for i in range(4):
            momentum[i] = int(momentum[i])


        print(momentum[0], momentum[1], momentum[2], momentum[3])

        av = (list(angular_velocities) + [""] * 4)[:4]
        mom = (list(momentum) + [0] * 4)[:4]
        try:
            self._log_writer.writerow([
                av[0], av[1], av[2], av[3],
                yaw_difference,
                current_gas,
                mom[0], mom[1], mom[2], mom[3],
            ])
            self._log_file.flush()
        except Exception as e:
            print(f"telemetry log write error: {e}")

        for i, wheel in enumerate(wheels):
            self._prev_velocities[i] = angular_velocities[i]
        self._write_car_wheels_state(momentum[0], momentum[1], momentum[2], momentum[3],
                                     angular_velocities[0], angular_velocities[1], angular_velocities[2], angular_velocities[3])
        command = {
            "AssistStats": {
                "assistWheel_FL": {
                    "drive": momentum[0],
                    "break": 0
                },
                "assistWheel_FR": {
                    "drive": momentum[1],
                    "break": 0
                },
                "assistWheel_RL": {
                    "drive": momentum[2],
                    "break": 0
                },
                "assistWheel_RR": {
                    "drive": momentum[3],
                    "break": 0
                }
            },
            "handBreak": False
        }

        self.send_message("robot.command", command)