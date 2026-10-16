# -*- coding: utf-8 -*-
"""
Приложение управления PID/NN сервером для Анрила и Ровера
"""

import sys
import json
import subprocess
from pathlib import Path

from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFormLayout, QLineEdit, QPushButton, QMessageBox, QLabel,
    QGridLayout, QTabWidget, QProgressBar, QSpinBox, QFrame,
    QStackedWidget, QScrollArea
)


# Скрываем консольное окно дочерних процессов на Windows
CREATE_NO_WINDOW = 0x08000000

def _no_window_kwargs() -> dict:
    import platform
    if platform.system() != "Windows":
        return {}
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = 0
    return {"creationflags": CREATE_NO_WINDOW, "startupinfo": si}

def get_base_dir() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def get_python_exe() -> str:
    if not getattr(sys, 'frozen', False):
        return sys.executable
    base = get_base_dir()
    candidates = [
        base / ".venv" / "Scripts" / "pythonw.exe",
        base / ".venv" / "Scripts" / "python.exe",
        base / "venv" / "Scripts" / "pythonw.exe",
        base / "venv" / "Scripts" / "python.exe",
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    import shutil
    python = shutil.which("pythonw") or shutil.which("python") or shutil.which("python3")
    if python:
        return python
    raise RuntimeError("Не найден python.exe — установите .venv рядом с gui.exe")


# ── Поток обучения нейронки ──────────────────────────────────────
class TrainThread(QThread):
    progress = pyqtSignal(int)
    log_line = pyqtSignal(str)
    finished_ok = pyqtSignal()
    finished_err = pyqtSignal(str)

    def __init__(self, script_path: Path, total_epochs: int = 600):
        super().__init__()
        self.script_path   = script_path
        self.total_epochs  = total_epochs
        self._process      = None
        self._stopped      = False

    def run(self):
        try:
            import os
            env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
            self._process = subprocess.Popen(
                [get_python_exe(), str(self.script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=env,
                **_no_window_kwargs()
            )
            for line in self._process.stdout:
                line = line.rstrip()
                self.log_line.emit(line)
                if line.startswith("Epoch"):
                    try:
                        ep = int(line.split()[1])
                        pct = min(int(ep / self.total_epochs * 100), 99)
                        self.progress.emit(pct)
                    except Exception:
                        pass
            self._process.wait()
            if self._stopped:
                return
            if self._process.returncode == 0:
                self.progress.emit(100)
                self.finished_ok.emit()
            else:
                self.finished_err.emit(f"Процесс завершился с кодом {self._process.returncode}")
        except Exception as e:
            if not self._stopped:
                self.finished_err.emit(str(e))

    def stop(self):
        self._stopped = True
        if self._process and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()


# ── Виджет колёс для Анрила (momentum + angular_velocity) ────────
class WheelsWidgetAnreal(QWidget):
    KEYS = [
        ("FL", "forward_left_wheel_momentum",          "forward_left_wheel_angular_velocity"),
        ("RL", "rear_left_wheel_momentum",             "rear_left_wheel_angular_velocity"),
        ("FR", "forward_right_wheel_momentum",         "forward_right_wheel_angular_velocity"),
        ("RR", "rear_right_wheel_momentum",            "rear_right_wheel_angular_velocity"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._fields = {}
        self._build_ui()

    def _make_field(self):
        f = QLineEdit("0")
        f.setReadOnly(True)
        f.setMaximumWidth(120)
        return f

    def _wheel_column(self, wheel_ids):
        WHEEL_GAP = 30
        box = QVBoxLayout()
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(2)
        for i, wid in enumerate(wheel_ids):
            _, mom_key, vel_key = next(r for r in self.KEYS if r[0] == wid)
            mom_f = self._make_field()
            vel_f = self._make_field()
            self._fields[wid] = (mom_f, vel_f)

            lbl_m = QLabel("Момент колеса:")
            lbl_m.setStyleSheet("font-size: 10px;")
            lbl_v = QLabel("Скорость вращения:")
            lbl_v.setStyleSheet("font-size: 10px;")

            box.addWidget(lbl_m)
            box.addWidget(mom_f)
            box.addWidget(lbl_v)
            box.addWidget(vel_f)
            if i < len(wheel_ids) - 1:
                box.addSpacing(WHEEL_GAP)

        w = QWidget()
        w.setLayout(box)
        return w

    def _build_ui(self):
        left_col  = self._wheel_column(["FL", "RL"])
        right_col = self._wheel_column(["FR", "RR"])

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        if getattr(sys, 'frozen', False):
            base = Path(sys.executable).resolve().parent
        else:
            base = Path(__file__).resolve().parent
        image_path = base / "car.jpg"
        if image_path.exists():
            pixmap = QPixmap(str(image_path))
            pixmap = pixmap.scaled(520, 340, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(pixmap)
            self.image_label.adjustSize()
        else:
            self.image_label.setText("car.jpg не найден")
            self.image_label.setStyleSheet("color: #aaa; font-size: 11px;")

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(0)
        grid.setVerticalSpacing(0)
        grid.addWidget(left_col,          0, 0, Qt.AlignVCenter | Qt.AlignRight)
        grid.addWidget(self.image_label,  0, 1, Qt.AlignCenter)
        grid.addWidget(right_col,         0, 2, Qt.AlignVCenter | Qt.AlignLeft)
        self.setLayout(grid)

    def update_values(self, data: dict):
        key_map = {
            "FL": ("forward_left_wheel_momentum",  "forward_left_wheel_angular_velocity"),
            "RL": ("rear_left_wheel_momentum",     "rear_left_wheel_angular_velocity"),
            "FR": ("forward_right_wheel_momentum", "forward_right_wheel_angular_velocity"),
            "RR": ("rear_right_wheel_momentum",    "rear_right_wheel_angular_velocity"),
        }
        for wid, (mom_key, vel_key) in key_map.items():
            mom_f, vel_f = self._fields[wid]
            mom_f.setText(str(data.get(mom_key, "0")))
            vel_f.setText(str(data.get(vel_key, "0")))

    def reset_values(self):
        for mom_f, vel_f in self._fields.values():
            mom_f.setText("0")
            vel_f.setText("0")


# ── Виджет колёс для Ровера (slip + angular_velocity) ────────────
class WheelsWidgetRover(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._fields = {}
        self._build_ui()

    def _make_field(self):
        f = QLineEdit("0")
        f.setReadOnly(True)
        f.setMaximumWidth(120)
        return f

    def _wheel_column(self, wheel_ids):
        WHEEL_GAP = 30
        box = QVBoxLayout()
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(2)
        for i, wid in enumerate(wheel_ids):
            slip_f = self._make_field()
            vel_f  = self._make_field()
            self._fields[wid] = (slip_f, vel_f)

            lbl_s = QLabel("Момент колеса:")
            lbl_s.setStyleSheet("font-size: 10px;")
            lbl_v = QLabel("Скорость вращения:")
            lbl_v.setStyleSheet("font-size: 10px;")

            box.addWidget(lbl_s)
            box.addWidget(slip_f)
            box.addWidget(lbl_v)
            box.addWidget(vel_f)
            if i < len(wheel_ids) - 1:
                box.addSpacing(WHEEL_GAP)

        w = QWidget()
        w.setLayout(box)
        return w

    def _build_ui(self):
        left_col  = self._wheel_column(["FL", "RL"])
        right_col = self._wheel_column(["FR", "RR"])

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        if getattr(sys, 'frozen', False):
            base = Path(sys.executable).resolve().parent
        else:
            base = Path(__file__).resolve().parent
        image_path = base / "car.jpg"
        if image_path.exists():
            pixmap = QPixmap(str(image_path))
            pixmap = pixmap.scaled(520, 340, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(pixmap)
            self.image_label.adjustSize()
        else:
            self.image_label.setText("car.jpg не найден")
            self.image_label.setStyleSheet("color: #aaa; font-size: 11px;")

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(0)
        grid.setVerticalSpacing(0)
        grid.addWidget(left_col,         0, 0, Qt.AlignVCenter | Qt.AlignRight)
        grid.addWidget(self.image_label, 0, 1, Qt.AlignCenter)
        grid.addWidget(right_col,        0, 2, Qt.AlignVCenter | Qt.AlignLeft)
        self.setLayout(grid)

    def update_values(self, data: dict):
        key_map = {
            "FL": ("forward_left_wheel_slip_magnitude",  "forward_left_wheel_angular_velocity"),
            "RL": ("rear_left_wheel_slip_magnitude",     "rear_left_wheel_angular_velocity"),
            "FR": ("forward_right_wheel_slip_magnitude", "forward_right_wheel_angular_velocity"),
            "RR": ("rear_right_wheel_slip_magnitude",    "rear_right_wheel_angular_velocity"),
        }
        for wid, (slip_key, vel_key) in key_map.items():
            slip_f, vel_f = self._fields[wid]
            slip_f.setText(str(data.get(slip_key, "0")))
            vel_f.setText(str(data.get(vel_key, "0")))

    def reset_values(self):
        for f1, f2 in self._fields.values():
            f1.setText("0")
            f2.setText("0")


# ── PID-виджет для Анрила (kp, kd) ──────────────────────────────
class AnrealPidWidget(QWidget):
    def __init__(self, wheels_state_path: Path, params_json_path: Path, parent=None):
        super().__init__(parent)
        self.wheels_state_path = wheels_state_path
        self.params_json_path  = params_json_path
        self.server_process    = None

        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(8, 4, 8, 8)

        form = QFormLayout()
        self.field_kp  = QLineEdit()
        self.field_kd  = QLineEdit()
        self.field_gas = QSpinBox()
        self.field_gas.setRange(0, 1000)
        self.field_gas.setValue(0)
        for f in [self.field_kp, self.field_kd]:
            f.setPlaceholderText("Введите значение")
        form.addRow("Коэффициент kp:", self.field_kp)
        form.addRow("Коэффициент kd:", self.field_kd)
        form.addRow("Газ (0–1000):", self.field_gas)
        layout.addLayout(form)

        btn_params = QHBoxLayout()
        self.save_btn = QPushButton("Сохранить параметры")
        self.load_btn = QPushButton("Загрузить параметры")
        self.save_btn.clicked.connect(self.on_save)
        self.load_btn.clicked.connect(self.on_load)
        btn_params.addWidget(self.save_btn)
        btn_params.addWidget(self.load_btn)
        btn_params.addStretch()
        layout.addLayout(btn_params)

        layout.addWidget(self._hline())

        self.wheels = WheelsWidgetAnreal()
        layout.addWidget(self.wheels)

        layout.addWidget(self._hline())

        btn_srv = QHBoxLayout()
        self.start_btn = QPushButton("Запустить сервер")
        self.close_btn = QPushButton("Остановить сервер")
        self.start_btn.clicked.connect(self.on_start)
        self.close_btn.clicked.connect(self.on_close)
        self.close_btn.setEnabled(False)
        btn_srv.addWidget(self.start_btn)
        btn_srv.addWidget(self.close_btn)
        layout.addLayout(btn_srv)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_display)
        self._timer.start(200)
        self._clear_state()

    def _hline(self):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        return line

    def _update_display(self):
        if not self.wheels_state_path.exists():
            return
        try:
            data = json.loads(self.wheels_state_path.read_text(encoding="utf-8"))
        except Exception:
            return
        self.wheels.update_values(data)

    def on_save(self):
        kp = self.field_kp.text().strip()
        kd = self.field_kd.text().strip()
        if not (kp and kd):
            QMessageBox.warning(self, "Ошибка", "Заполните поля")
            return
        try:
            kp, kd = float(kp), float(kd)
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Вводимые значения должны быть числами")
            return
        if kp <= 0 or kd <= 0:
            QMessageBox.warning(self, "Ошибка", "Вводимые значения должны быть больше 0")
            return
        gas = self.field_gas.value()
        self.params_json_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.params_json_path.write_text(
                json.dumps({"kp": kp, "kd": kd, "gas": gas}, indent=4), encoding="utf-8")
            QMessageBox.information(self, "Готово", "Параметры сохранены")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить: {e}")

    def on_load(self):
        if not self.params_json_path.exists():
            QMessageBox.warning(self, "Ошибка", "Файл не найден")
            return
        try:
            cfg = json.loads(self.params_json_path.read_text(encoding="utf-8"))
        except Exception:
            QMessageBox.warning(self, "Ошибка", "Не удалось прочитать файл")
            return
        self.field_kp.setText(str(cfg.get("kp", "")))
        self.field_kd.setText(str(cfg.get("kd", "")))
        if "gas" in cfg:
            gas_val = int(cfg["gas"])
            gas_val = max(0, min(1000, gas_val))
            self.field_gas.setValue(gas_val)

    def on_start(self):
        script = get_base_dir() / "main_for_anreal.py"
        if not script.exists():
            QMessageBox.warning(self, "Ошибка", "Файл main_for_anreal.py не найден")
            return
        import os
        root = str(script.parent.parent)
        env = {**os.environ, "PYTHONPATH": root}
        self.server_process = subprocess.Popen(
            [get_python_exe(), str(script)],
            cwd=root,
            env=env,
            **_no_window_kwargs()
        )
        self.save_btn.setEnabled(False)
        self.load_btn.setEnabled(False)
        self.start_btn.setEnabled(False)
        self.close_btn.setEnabled(True)

    def on_close(self):
        if self.server_process:
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
            self.server_process = None
        self._clear_state()
        self.wheels.reset_values()
        self.save_btn.setEnabled(True)
        self.load_btn.setEnabled(True)
        self.start_btn.setEnabled(True)
        self.close_btn.setEnabled(False)

    def _clear_state(self):
        data = {k: 0 for k in [
            "forward_left_wheel_momentum",          "forward_right_wheel_momentum",
            "rear_left_wheel_momentum",             "rear_right_wheel_momentum",
            "forward_left_wheel_angular_velocity",  "forward_right_wheel_angular_velocity",
            "rear_left_wheel_angular_velocity",     "rear_right_wheel_angular_velocity",
        ]}
        try:
            self.wheels_state_path.parent.mkdir(parents=True, exist_ok=True)
            self.wheels_state_path.write_text(json.dumps(data), encoding="utf-8")
        except Exception:
            pass


# ── NN-виджет для Анрила (газ с сохранением/загрузкой) ──────────
class AnrealNNWidget(QWidget):
    def __init__(self, wheels_state_path: Path, params_json_path: Path, parent=None):
        super().__init__(parent)
        self.wheels_state_path = wheels_state_path
        self.params_json_path  = params_json_path
        self.server_process    = None

        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(8, 4, 8, 8)

        form = QFormLayout()
        self.field_gas = QSpinBox()
        self.field_gas.setRange(0, 1000)
        self.field_gas.setValue(0)
        form.addRow("Газ (0–1000):", self.field_gas)
        layout.addLayout(form)

        btn_params = QHBoxLayout()
        self.save_btn = QPushButton("Сохранить параметры")
        self.load_btn = QPushButton("Загрузить параметры")
        self.save_btn.clicked.connect(self.on_save)
        self.load_btn.clicked.connect(self.on_load)
        btn_params.addWidget(self.save_btn)
        btn_params.addWidget(self.load_btn)
        btn_params.addStretch()
        layout.addLayout(btn_params)

        layout.addWidget(self._hline())

        self.wheels = WheelsWidgetAnreal()
        layout.addWidget(self.wheels)

        layout.addWidget(self._hline())

        btn_srv = QHBoxLayout()
        self.start_btn = QPushButton("Запустить сервер")
        self.close_btn = QPushButton("Остановить сервер")
        self.start_btn.clicked.connect(self.on_start)
        self.close_btn.clicked.connect(self.on_close)
        self.close_btn.setEnabled(False)
        btn_srv.addWidget(self.start_btn)
        btn_srv.addWidget(self.close_btn)
        layout.addLayout(btn_srv)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_display)
        self._timer.start(200)
        self._clear_state()

    def _hline(self):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        return line

    def _update_display(self):
        if not self.wheels_state_path.exists():
            return
        try:
            data = json.loads(self.wheels_state_path.read_text(encoding="utf-8"))
        except Exception:
            return
        self.wheels.update_values(data)

    def on_save(self):
        gas = self.field_gas.value()
        self.params_json_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.params_json_path.write_text(
                json.dumps({"gas": gas}, indent=4), encoding="utf-8")
            QMessageBox.information(self, "Готово", "Параметры сохранены")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить: {e}")

    def on_load(self):
        if not self.params_json_path.exists():
            QMessageBox.warning(self, "Ошибка", "Файл не найден")
            return
        try:
            cfg = json.loads(self.params_json_path.read_text(encoding="utf-8"))
        except Exception:
            QMessageBox.warning(self, "Ошибка", "Не удалось прочитать файл")
            return
        if "gas" not in cfg:
            QMessageBox.warning(self, "Ошибка", "В файле нет значения газа")
            return
        gas_val = int(cfg["gas"])
        gas_val = max(0, min(1000, gas_val))
        self.field_gas.setValue(gas_val)

    def on_start(self):
        script = get_base_dir() / "main_for_anreal_nn.py"
        if not script.exists():
            QMessageBox.warning(self, "Ошибка", "Файл main_for_anreal_nn.py не найден")
            return
        import os
        root = str(script.parent.parent)
        env = {**os.environ, "THROTTLE_VALUE": str(self.field_gas.value()), "PYTHONPATH": root}
        self.server_process = subprocess.Popen(
            [get_python_exe(), str(script)],
            env=env,
            cwd=root,
            **_no_window_kwargs()
        )
        self.save_btn.setEnabled(False)
        self.load_btn.setEnabled(False)
        self.start_btn.setEnabled(False)
        self.close_btn.setEnabled(True)

    def on_close(self):
        if self.server_process:
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
            self.server_process = None
        self._clear_state()
        self.wheels.reset_values()
        self.save_btn.setEnabled(True)
        self.load_btn.setEnabled(True)
        self.start_btn.setEnabled(True)
        self.close_btn.setEnabled(False)

    def _clear_state(self):
        data = {k: 0 for k in [
            "forward_left_wheel_momentum",         "forward_right_wheel_momentum",
            "rear_left_wheel_momentum",            "rear_right_wheel_momentum",
            "forward_left_wheel_angular_velocity", "forward_right_wheel_angular_velocity",
            "rear_left_wheel_angular_velocity",    "rear_right_wheel_angular_velocity",
        ]}
        try:
            self.wheels_state_path.parent.mkdir(parents=True, exist_ok=True)
            self.wheels_state_path.write_text(json.dumps(data), encoding="utf-8")
        except Exception:
            pass


# ── Простой виджет запуска (без параметров) ──────────────────────
class SimpleServerWidget(QWidget):
    def __init__(self, script_name: str, wheels_state_path: Path,
                 mode: str = "rover",
                 show_gas: bool = False,
                 params_json_path: Path = None,
                 joystick_warning: bool = False,
                 parent=None):
        super().__init__(parent)
        self.script_name       = script_name
        self.wheels_state_path = wheels_state_path
        self.show_gas          = show_gas
        self.params_json_path  = params_json_path
        self.mode              = mode
        self.server_process    = None

        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(8, 4, 8, 8)

        if joystick_warning:
            warn = QLabel("Необходимо подключить джойстик перед запуском сервера")
            warn.setStyleSheet(
                "background: #fff8e1; color: #795548; padding: 3px 6px;"
                "border: 1px solid #ffe082; border-radius: 3px; font-size: 13px;")
            warn.setAlignment(Qt.AlignCenter)
            layout.addWidget(warn)

        if show_gas:
            gas_row = QHBoxLayout()
            gas_row.addWidget(QLabel("Газ:"))
            self.gas_spin = QSpinBox()
            self.gas_spin.setRange(0, 1000)
            self.gas_spin.setValue(0)
            gas_row.addWidget(self.gas_spin)
            gas_row.addWidget(QLabel("(0–1000)"))
            gas_row.addStretch()
            layout.addLayout(gas_row)

        layout.addWidget(self._hline())

        if mode == "anreal":
            self.wheels = WheelsWidgetAnreal()
        else:
            self.wheels = WheelsWidgetRover()
        layout.addWidget(self.wheels)

        layout.addWidget(self._hline())

        btn_row = QHBoxLayout()
        self.start_btn = QPushButton("Запустить сервер")
        self.close_btn = QPushButton("Остановить сервер")
        self.start_btn.clicked.connect(self.on_start)
        self.close_btn.clicked.connect(self.on_close)
        self.close_btn.setEnabled(False)
        btn_row.addWidget(self.start_btn)
        btn_row.addWidget(self.close_btn)
        layout.addLayout(btn_row)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update)
        self._timer.start(200)
        self._clear_state()

    def _hline(self):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        return line

    def _update(self):
        if not self.wheels_state_path.exists():
            return
        try:
            data = json.loads(self.wheels_state_path.read_text(encoding="utf-8"))
            self.wheels.update_values(data)
        except Exception:
            pass

    def on_start(self):
        script = get_base_dir() / self.script_name
        if not script.exists():
            QMessageBox.warning(self, "Ошибка", f"Файл {self.script_name} не найден")
            return
        import os
        env = dict(os.environ)
        if self.show_gas:
            gas = self.gas_spin.value()
            env["THROTTLE_VALUE"] = str(gas)
            if self.params_json_path is not None:
                try:
                    cfg = {}
                    if self.params_json_path.exists():
                        cfg = json.loads(self.params_json_path.read_text(encoding="utf-8"))
                    cfg["gas"] = gas
                    self.params_json_path.parent.mkdir(parents=True, exist_ok=True)
                    self.params_json_path.write_text(json.dumps(cfg, indent=4), encoding="utf-8")
                except Exception:
                    pass
        root = str(script.parent.parent)
        env["PYTHONPATH"] = root
        self.server_process = subprocess.Popen(
            [get_python_exe(), str(script)],
            env=env,
            cwd=root,
            **_no_window_kwargs()
        )
        self.start_btn.setEnabled(False)
        self.close_btn.setEnabled(True)

    def on_close(self):
        if self.server_process:
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
            self.server_process = None
        self.wheels.reset_values()
        self._clear_state()
        self.start_btn.setEnabled(True)
        self.close_btn.setEnabled(False)

    def _clear_state(self):
        if self.mode == "anreal":
            keys = [
                "forward_left_wheel_momentum",         "forward_right_wheel_momentum",
                "rear_left_wheel_momentum",            "rear_right_wheel_momentum",
                "forward_left_wheel_angular_velocity", "forward_right_wheel_angular_velocity",
                "rear_left_wheel_angular_velocity",    "rear_right_wheel_angular_velocity",
            ]
        else:
            keys = [
                "forward_left_wheel_slip_magnitude",   "forward_right_wheel_slip_magnitude",
                "rear_left_wheel_slip_magnitude",      "rear_right_wheel_slip_magnitude",
                "forward_left_wheel_angular_velocity", "forward_right_wheel_angular_velocity",
                "rear_left_wheel_angular_velocity",    "rear_right_wheel_angular_velocity",
            ]
        data = {k: 0 for k in keys}
        try:
            self.wheels_state_path.parent.mkdir(parents=True, exist_ok=True)
            self.wheels_state_path.write_text(json.dumps(data), encoding="utf-8")
        except Exception:
            pass


# ── Виджет обучения нейронки ─────────────────────────────────────
class TrainWidget(QWidget):
    def __init__(self, train_script_path: Path, params_json_path: Path, parent=None):
        super().__init__(parent)
        self.train_script_path = train_script_path
        self.params_json_path  = params_json_path
        self.train_thread      = None

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignTop)

        form = QFormLayout()
        self.field_epochs = QSpinBox()
        self.field_epochs.setRange(1, 10000)
        self.field_epochs.setValue(1)

        self.field_lr = QLineEdit("")
        self.field_lr.setPlaceholderText("например: 0.001")

        form.addRow("Количество эпох:", self.field_epochs)
        form.addRow("Скорость обучения (LR):", self.field_lr)
        layout.addLayout(form)

        btn_params = QHBoxLayout()
        self.save_params_btn = QPushButton("Сохранить параметры")
        self.load_params_btn = QPushButton("Загрузить параметры")
        self.save_params_btn.clicked.connect(self.on_save_params)
        self.load_params_btn.clicked.connect(self.on_load_params)
        btn_params.addWidget(self.save_params_btn)
        btn_params.addWidget(self.load_params_btn)
        btn_params.addStretch()
        layout.addLayout(btn_params)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Ожидание запуска")
        layout.addWidget(self.progress_bar)

        self.log_label = QLabel("")
        self.log_label.setWordWrap(True)
        self.log_label.setStyleSheet("font-size: 10px; color: #444; font-family: monospace;")
        self.log_label.setMinimumHeight(50)
        layout.addWidget(self.log_label)

        btn_row = QHBoxLayout()
        self.train_btn = QPushButton("Запустить обучение")
        self.train_btn.setMinimumHeight(32)
        self.train_btn.clicked.connect(self.on_train)
        self.stop_btn = QPushButton("Остановить")
        self.stop_btn.setMinimumHeight(32)
        self.stop_btn.clicked.connect(self.on_stop)
        self.stop_btn.setEnabled(False)
        btn_row.addWidget(self.train_btn)
        btn_row.addWidget(self.stop_btn)
        layout.addLayout(btn_row)

    def _validate_lr(self, lr_text: str):
        """Возвращает float(lr) если валиден и > 0, иначе показывает предупреждение и None."""
        try:
            lr = float(lr_text)
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Вводимые значения должны быть числом")
            return None
        if lr <= 0:
            QMessageBox.warning(self, "Ошибка", "Вводимые значения должны быть больше 0")
            return None
        return lr

    def on_save_params(self):
        lr_text = self.field_lr.text().strip()
        lr = self._validate_lr(lr_text)
        if lr is None:
            return
        epochs = self.field_epochs.value()
        if epochs <= 0:
            QMessageBox.warning(self, "Ошибка", "Вводимые значения должны быть больше 0")
            return
        self.params_json_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.params_json_path.write_text(
                json.dumps({"epochs": epochs, "lr": lr}, indent=4), encoding="utf-8")
            QMessageBox.information(self, "Готово", "Параметры сохранены")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить: {e}")

    def on_load_params(self):
        if not self.params_json_path.exists():
            QMessageBox.warning(self, "Ошибка", "Файл не найден")
            return
        try:
            cfg = json.loads(self.params_json_path.read_text(encoding="utf-8"))
        except Exception:
            QMessageBox.warning(self, "Ошибка", "Не удалось прочитать файл")
            return
        if "epochs" in cfg:
            epochs_val = int(cfg["epochs"])
            epochs_val = max(1, epochs_val)
            self.field_epochs.setValue(epochs_val)
        if "lr" in cfg:
            self.field_lr.setText(str(cfg["lr"]))

    def on_train(self):
        if not self.train_script_path.exists():
            QMessageBox.warning(self, "Ошибка", f"Скрипт не найден:\n{self.train_script_path}")
            return
        lr_text = self.field_lr.text().strip()
        lr = self._validate_lr(lr_text)
        if lr is None:
            return
        epochs = self.field_epochs.value()
        if epochs <= 0:
            QMessageBox.warning(self, "Ошибка", "Вводимые значения должны быть больше 0")
            return
        self.params_json_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.params_json_path.write_text(
                json.dumps({"epochs": epochs, "lr": lr}, indent=4), encoding="utf-8")
        except Exception:
            pass
        self._total_epochs = epochs
        self.train_thread = TrainThread(self.train_script_path, total_epochs=epochs)
        self.train_thread.progress.connect(self.progress_bar.setValue)
        self.train_thread.log_line.connect(self.log_label.setText)
        self.train_thread.finished_ok.connect(self._on_done)
        self.train_thread.finished_err.connect(self._on_error)
        self.train_thread.start()
        self.train_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.save_params_btn.setEnabled(False)
        self.load_params_btn.setEnabled(False)
        self.progress_bar.setFormat("Обучение... %p%")
        self.progress_bar.setValue(0)

    def on_stop(self):
        if self.train_thread:
            self.train_thread.stop()
            self.train_thread = None
        self.train_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.save_params_btn.setEnabled(True)
        self.load_params_btn.setEnabled(True)
        self.progress_bar.setFormat("Остановлено")
        QMessageBox.information(self, "Остановлено", "Обучение остановлено")

    def _on_done(self):
        self.progress_bar.setFormat("Обучение завершено")
        self.train_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.save_params_btn.setEnabled(True)
        self.load_params_btn.setEnabled(True)
        QMessageBox.information(self, "Готово", "Обучение завершено!")

    def _on_error(self, msg):
        self.progress_bar.setFormat("Ошибка")
        self.train_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.save_params_btn.setEnabled(True)
        self.load_params_btn.setEnabled(True)
        QMessageBox.warning(self, "Ошибка", msg)


# ── Меню выбора режима ───────────────────────────────────────────
class ModeMenuWidget(QWidget):
    def __init__(self, title: str, btn_labels: list, on_select, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(14)

        hdr = QLabel(title)
        hdr.setFont(QFont("", 13, QFont.Bold))
        hdr.setAlignment(Qt.AlignCenter)
        layout.addWidget(hdr)
        layout.addSpacing(16)

        for idx, label in enumerate(btn_labels):
            btn = QPushButton(label)
            btn.setMinimumHeight(44)
            btn.setMinimumWidth(300)
            btn.clicked.connect(lambda checked, i=idx: on_select(i))
            layout.addWidget(btn, alignment=Qt.AlignCenter)


# ── Вкладка Анрил ────────────────────────────────────────────────
class AnrealTab(QWidget):
    def __init__(self, base_dir: Path, parent=None):
        super().__init__(parent)

        root_dir          = base_dir.parent
        wheels_state      = root_dir / "src" / "modules" / "implementation" / "pid_control_for_anreal" / "car_wheels_state.json"
        params_json       = root_dir / "src" / "modules" / "implementation" / "pid_control_for_anreal" / "params.json"
        params_json_nn    = root_dir / "src" / "modules" / "implementation" / "nn_pid_control_for_anreal" / "params.json"
        wheels_state_nn   = root_dir / "src" / "modules" / "implementation" / "nn_pid_control_for_anreal" / "car_wheels_state.json"
        params_json_train = base_dir / "params_for_train_nn_for_anreal.json"
        train_script      = base_dir / "train_nn_for_anreal.py"

        self.stack = QStackedWidget()

        self.menu = ModeMenuWidget(
            title="3D модель",
            btn_labels=[
                "Запуск сервера через PID",
                "Запуск сервера с нейронной сетью",
                "Обучение нейронной сети",
            ],
            on_select=self._go_to
        )

        self.pid_page   = self._wrap(AnrealPidWidget(wheels_state, params_json))
        self.nn_page    = self._wrap(AnrealNNWidget(wheels_state_nn, params_json_nn))
        self.train_page = self._wrap(TrainWidget(train_script, params_json_train))

        for w in [self.menu, self.pid_page, self.nn_page, self.train_page]:
            self.stack.addWidget(w)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stack)

    def _wrap(self, widget: QWidget) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        back_btn = QPushButton("Назад")
        back_btn.setMaximumWidth(90)
        back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        layout.addWidget(back_btn)
        layout.addWidget(widget)
        return container

    def _go_to(self, idx: int):
        self.stack.setCurrentIndex(idx + 1)


# ── Вкладка Ровер ────────────────────────────────────────────────
class RoverTab(QWidget):
    def __init__(self, base_dir: Path, parent=None):
        super().__init__(parent)

        root_dir          = base_dir.parent
        wheels_state      = root_dir / "src" / "modules" / "implementation" / "control_for_rover" / "car_wheels_state.json"
        wheels_state_nn   = root_dir / "src" / "modules" / "implementation" / "nn_control_for_rover" / "car_wheels_state.json"
        params_json_train = base_dir / "params_for_train_nn_for_rover.json"
        train_script      = base_dir / "train_nn_for_rover.py"

        self.stack = QStackedWidget()

        self.menu = ModeMenuWidget(
            title="Ровер",
            btn_labels=[
                "Запуск сервера (обычный алгоритм)",
                "Запуск сервера с нейронной сетью",
                "Обучение нейронной сети",
            ],
            on_select=self._go_to
        )

        self.algo_page  = self._wrap(SimpleServerWidget("main_for_rover.py",    wheels_state,    mode="rover", joystick_warning=True))
        self.nn_page    = self._wrap(SimpleServerWidget("main_for_rover_nn.py", wheels_state_nn, mode="rover", joystick_warning=True))
        self.train_page = self._wrap(TrainWidget(train_script, params_json_train))

        for w in [self.menu, self.algo_page, self.nn_page, self.train_page]:
            self.stack.addWidget(w)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stack)

    def _wrap(self, widget: QWidget) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        back_btn = QPushButton("Назад")
        back_btn.setMaximumWidth(90)
        back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        layout.addWidget(back_btn)
        layout.addWidget(widget)
        return container

    def _go_to(self, idx: int):
        self.stack.setCurrentIndex(idx + 1)


# ── Вкладка «Информация» ─────────────────────────────────────────
class AboutTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        outer.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)

        layout = QVBoxLayout(content)
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(36, 24, 36, 24)
        layout.setSpacing(6)

        # ── Заголовок ──
        title = QLabel("Управление серверами и запуск обучения моделей нейронных сетей")
        title.setFont(QFont("", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setWordWrap(True)
        layout.addWidget(title)

        layout.addSpacing(8)

        # ── Общее описание ──
        self._add_text(layout,
            "Данное приложение позволяет управлять 3D моделью и ровером с помощью готовых "
            "алгоритмов и обученных нейронных сетей для преодоления диагонального вывешивания. "
            "Также предоставлена возможность обучить нейронную сеть со своими параметрами обучения."
        )

        layout.addSpacing(6)
        layout.addWidget(self._hline())

        # ── Раздел 3D модель ──
        self._add_section(layout, "3D модель")
        self._add_text(layout, "В данной вкладке осуществлены следующие возможности:")
        layout.addSpacing(2)

        self._add_bullet(layout, "Запуск сервера через PID",
            "В данном разделе осуществляется управление 3D моделью через PID-регулятор. "
            "Предоставляется возможность загружать параметры регулятора и силу нажатия газа, "
            "а также подбирать их самостоятельно. Для загрузки параметров следует нажать кнопку "
            "«Загрузить параметры», для сохранения — «Сохранить параметры». Для запуска алгоритма "
            "необходимо нажать «Запустить сервер», для остановки — «Остановить сервер». "
            "В полях рядом с изображением машины при запуске сервера отображаются моменты "
            "на колёсах и скорости их вращения в режиме реального времени."
        )

        self._add_bullet(layout, "Запуск сервера с нейронной сетью",
            "В данном разделе осуществляется управление 3D моделью через нейронную сеть. "
            "Предоставляется возможность загружать силу нажатия газа или подбирать её самостоятельно. "
            "Для загрузки параметров следует нажать «Загрузить параметры», для сохранения — "
            "«Сохранить параметры». Для запуска нейронной сети на серверной части необходимо "
            "нажать «Запустить сервер»."
        )

        self._add_bullet(layout, "Обучение нейронной сети",
            "В данном разделе осуществляется обучение нейронной сети. Параметры обучения можно "
            "загрузить кнопкой «Загрузить параметры» или задать вручную и сохранить кнопкой "
            "«Сохранить параметры». Для запуска обучения нажмите «Запустить обучение», "
            "для досрочной остановки — «Остановить». По завершении обучения выводится путь "
            "к сохранённой наилучшей модели. Данные для обучения уже заданы."
        )

        layout.addSpacing(4)
        layout.addWidget(self._hline())

        # ── Раздел Ровер ──
        self._add_section(layout, "Ровер")
        layout.addSpacing(2)

        self._add_bullet(layout, "Запуск сервера (обычный алгоритм)",
            "В данном разделе осуществляется запуск алгоритма для управления ровером. "
            "Подбор параметров не предусмотрен. Перед запуском сервера необходимо убедиться "
            "в подключении джойстика к ПК. Поля вокруг изображения машины аналогичны "
            "тем, что используются в разделах для 3D модели."
        )

        self._add_bullet(layout, "Запуск сервера с нейронной сетью",
            "В данном разделе осуществляется управление ровером с использованием "
            "предобученных нейронных сетей."
        )

        self._add_bullet(layout, "Обучение нейронной сети",
            "Здесь предоставляется возможность обучения нейронной сети для управления ровером "
            "с подбором параметров обучения. Доступные действия аналогичны разделу обучения "
            "для 3D модели."
        )

        layout.addStretch()

    # ── Вспомогательные методы ──────────────────────────────────

    def _hline(self):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        return line

    def _add_section(self, layout, text):
        lbl = QLabel(text)
        lbl.setFont(QFont("", 12, QFont.Bold))
        lbl.setStyleSheet("margin-top: 6px; margin-bottom: 2px;")
        layout.addWidget(lbl)

    def _add_text(self, layout, text):
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setStyleSheet("font-size: 12px; color: #111;")
        layout.addWidget(lbl)

    def _add_bullet(self, layout, title, body):
        title_lbl = QLabel(f"• <b>{title}</b>")
        title_lbl.setTextFormat(Qt.RichText)
        title_lbl.setWordWrap(True)
        title_lbl.setStyleSheet("font-size: 12px; margin-left: 8px; margin-top: 4px;")
        layout.addWidget(title_lbl)

        body_lbl = QLabel(body)
        body_lbl.setWordWrap(True)
        body_lbl.setStyleSheet("font-size: 12px; margin-left: 22px; margin-bottom: 4px; color: #222;")
        layout.addWidget(body_lbl)


# ── Главное окно ─────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Управление сервером")
        self.resize(820, 700)

        base_dir = get_base_dir()
        tabs = QTabWidget()
        tabs.addTab(AnrealTab(base_dir), "3D модель")
        tabs.addTab(RoverTab(base_dir),  "Ровер")
        tabs.addTab(AboutTab(),          "Информация")
        self.setCentralWidget(tabs)

    def closeEvent(self, event):
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()