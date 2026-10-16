from src.modules.base.base_module.base_module import BaseModule
from src.modules.base.decorator.decorator import *
import numpy as np
import torch
import torch.nn as nn
import os
from pathlib import Path
import csv

# class MomentumLSTM(nn.Module):
#     def __init__(self):
#         super().__init__()
#         self.lstm = nn.LSTM(
#             input_size=6,
#             hidden_size=64,
#             num_layers=2,
#             batch_first=True,
#             dropout=0.1,
#         )
#         self.head = nn.Sequential(
#             nn.Linear(64, 32),
#             nn.ReLU(),
#             nn.Linear(32, 4),
#             nn.Sigmoid(),
#         )
#
#     def forward(self, x, state=None):
#         out, state = self.lstm(x, state)
#         last = out[:, -1, :]
#         return self.head(last), state

class MomentumRNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.rnn = nn.RNN(
            input_size=6,
            hidden_size=64,
            num_layers=2,
            batch_first=True,
            dropout=0.1,
            nonlinearity="tanh",
        )
        self.head = nn.Sequential(
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 4),
            nn.Sigmoid(),
        )

    def forward(self, x, state=None):
        out, state = self.rnn(x, state)
        last = out[:, -1, :]
        return self.head(last), state


@infinite_loop(1)
class NNPidControlForAnrealModule(BaseModule):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._params_path = Path(__file__).resolve().parent / "params.json"
        self._car_wheels_state_path = Path(__file__).resolve().parent / "car_wheels_state.json"

        with open(self._params_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self._current_gas = data['gas']

        self._min_v_car    = 0.00001
        self._wheel_radius = 0.36
        self._target_yaw   = None

        #lstm
        # model_path = os.path.join(os.path.dirname(__file__), "momentum_lstm_20.pt")  # ← имя файла
        # self._model = MomentumLSTM()  # ← класс
        # self._lstm_state = None

        #rnn
        model_path = os.path.join(os.path.dirname(__file__), "momentum_rnn.pt")
        self._model = MomentumRNN()

        checkpoint = torch.load(model_path, weights_only=False)

        self._model.load_state_dict(checkpoint["model_state"])

        self._model.eval()

        self._scaler_X   = checkpoint["scaler_X"]
        self._scaler_y   = checkpoint["scaler_y"]
        self._input_cols = checkpoint["input_cols"]

        # ── Добавляем состояние для памяти между вызовами ────────
        self._rnn_state = None
        log_dir = "test/telemetry_from_anreal_nn_from_trip"
        os.makedirs(log_dir, exist_ok=True)
        self._log_path = os.path.join(log_dir, "telemetry_log_gas_475.csv")
        file_is_new = (not os.path.exists(self._log_path)) or os.path.getsize(self._log_path) == 0
        self._log_file = open(self._log_path, "a", newline="")
        self._log_writer = csv.writer(self._log_file)
        if file_is_new:
            self._log_writer.writerow([
                "angular_velocity_fl_mps", "angular_velocity_fr_mps", "angular_velocity_rl_mps",
                "angular_velocity_rr_mps",  # скорость колёс в м/с
                "yaw_difference",
                "initial_momentum",
                "momentum_fl", "momentum_fr", "momentum_rl", "momentum_rr",
            ])
            self._log_file.flush()

    # def reset_rnn(self):
    #     """Сбросить память — вызывать при старте нового заезда."""
    #     self._rnn_state = None

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

    def _predict_momentum(self, angular_velocities, yaw_difference, initial_momentum):
        measurement = {
            "angular_velocity_fl_mps": angular_velocities[0],
            "angular_velocity_fr_mps": angular_velocities[1],
            "angular_velocity_rl_mps": angular_velocities[2],
            "angular_velocity_rr_mps": angular_velocities[3],
            "yaw_difference": yaw_difference,
            "initial_momentum": initial_momentum,
        }

        raw = np.array([[measurement[c] for c in self._input_cols]], dtype=np.float32)
        x_norm = self._scaler_X.transform(raw).astype(np.float32)
        x_tensor = torch.from_numpy(x_norm).unsqueeze(1)  # (1, 1, 6)

        with torch.no_grad():
            #lstm
            # y_norm, self._lstm_state = self._model(x_tensor, self._lstm_state)

            #rnn
            y_norm, self._rnn_state = self._model(x_tensor, self._rnn_state)

        result = self._scaler_y.inverse_transform(y_norm.numpy())[0]
        return [int(np.clip(result[i], 0, 1000)) for i in range(4)]

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

        current_gas = self._current_gas

        momentum = self._predict_momentum(angular_velocities, yaw_difference, current_gas)

        self._write_car_wheels_state(momentum[0], momentum[1], momentum[2], momentum[3],
                                     angular_velocities[0], angular_velocities[1], angular_velocities[2], angular_velocities[3])

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