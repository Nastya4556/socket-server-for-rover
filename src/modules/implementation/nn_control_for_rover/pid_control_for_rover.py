from src.modules.base.base_module.base_module import BaseModule
from src.modules.base.decorator.decorator import *

import numpy as np
import csv
import os
from datetime import datetime
import torch
import torch.nn as nn
import time

# ------------------Архитектура RNN----------------------------------
HIDDEN_SIZE = 64
NUM_LAYERS = 2

class MomentumRNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.rnn = nn.RNN(
            input_size=5,  # delta_tl, delta_tr, delta_bl, delta_br, current_gas
            hidden_size=HIDDEN_SIZE,
            num_layers=NUM_LAYERS,
            batch_first=True,
            dropout=0.1,
            nonlinearity="tanh",
        )
        self.head = nn.Sequential(
            nn.Linear(HIDDEN_SIZE, 32),
            nn.ReLU(),
            nn.Linear(32, 4),  # momentum_tl, momentum_tr, momentum_bl, momentum_br
            nn.Sigmoid(),
        )

    def forward(self, x, state=None):
        out, state = self.rnn(x, state)
        # head применяется ко всей последовательности — совпадает с тем,
        # как модель обучалась (TBPTT, loss по каждому шагу чанка)
        pred_seq = self.head(out)  # (batch, seq, 4)
        return pred_seq, state


class RealtimePredictor:
    def __init__(self, checkpoint_path="momentum_rnn.pt"):
        # абсолютный путь относительно файла модуля — не зависит от cwd процесса
        if not os.path.isabs(checkpoint_path):
            checkpoint_path = os.path.join(os.path.dirname(__file__), checkpoint_path)

        checkpoint = torch.load(checkpoint_path, weights_only=False, map_location="cpu")

        self.net = MomentumRNN()
        self.net.load_state_dict(checkpoint["model_state"])
        self.net.eval()

        self.sx = checkpoint["scaler_X"]
        self.sy = checkpoint["scaler_y"]
        self.state = None

    def reset(self):
        """Сбросить скрытое состояние — вызывать при старте нового заезда/сессии."""
        self.state = None

    def predict_one(self, deltas: list, current_gas: int) -> list:
        """
        deltas      — список из 4 float [tl, tr, bl, br]
        current_gas — int (1000–2000)
        Возвращает список из 4 int momentum [tl, tr, bl, br]
        """
        raw = np.array([[*deltas, current_gas]], dtype=np.float32)
        x_norm = self.sx.transform(raw).astype(np.float32)
        x_tensor = torch.from_numpy(x_norm).unsqueeze(1)  # (1, 1, 5)

        with torch.no_grad():
            y_norm_seq, self.state = self.net(x_tensor, self.state)

        y_norm = y_norm_seq[:, -1, :]  # единственный шаг последовательности
        result = self.sy.inverse_transform(y_norm.numpy())[0]
        return [int(np.clip(round(v), 1000, 2000)) for v in result]
#----------------------------------------------------------------------------

@infinite_loop(0.02)
class NNControlForRoverModule(BaseModule):
    ready_for_interface = True
    accepts_any_input = True

    @classmethod
    def config_schema(cls):
        return dict()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._min_v_car = 0.00001

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
        self._ticks_for_check_hanging_threshold = 1

        self._ticks_for_check_grounded = 0
        self._step_for_momentum = 20

        self._prev_momentum_deltas = [None, None, None, None]

        self._message_from_joystick = None

        self._prev_gas = 1500

        # rnn
        self._predictor = RealtimePredictor("momentum_rnn.pt")
        self._predictor.reset()

        self._telemetry_dir = "test/telemetry_from_rover_nn_from_trip"
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

        now = time.monotonic()
        print(f"telemetry interval on server: {now - getattr(self, '_last_telem_time', now):.3f}")
        self._last_telem_time = now

        if self._message_from_joystick is None:
            return

        current_gas = int(1500 + float(self._message_from_joystick["Ось 1"]) * 500)
        current_turning = int(1500 + float(self._message_from_joystick["Ось 3"]) * 500)

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

        if len(deltas) > 0:
            positive = [a for a in deltas if a > 0]

            if positive:
                car_velocity = min(positive)
            else:
                car_velocity = self._min_v_car
        else:
            car_velocity = self._min_v_car

        for i in range(len(deltas)):
            print(deltas[i] - car_velocity)
            if abs(deltas[i]) - car_velocity > self._eps_for_acceleration_difference:
                lifted.append(i)
            else:
                grounded.append(i)

        #----------------------rnn--------------------------------------------------
        if len(lifted) > 0:
            momentum = self._predictor.predict_one(deltas, current_gas)
        else:
            momentum = [current_gas, current_gas, current_gas, current_gas]
        for i in range(len(momentum)):
            momentum[i] = int(np.clip(momentum[i], 1500, 2000))

        all_current = 200
        buf = f'{{"all_current": {all_current},"tl": {momentum[0]}, "tr": {momentum[1]}, "bl":{momentum[2]},  "br": {momentum[3]}, "st": {current_turning}}}'
        #----------------------------------------------------------------------------

        print(buf)
        message = {"com": buf}

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
