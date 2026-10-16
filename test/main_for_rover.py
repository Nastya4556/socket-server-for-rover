from src import modules as mods
from src import infinite_loop
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent

ManagerModule = mods.base.ManagerModule
CarModule = mods.implementation.CarModule
ClientIOModule = mods.implementation.ClientIOModule
ConsoleLogModule = mods.implementation.ConsoleLogModule
ControllerModule = mods.implementation.CarControllerModule
RobotIOModule = mods.implementation.RobotIOModule
RobotWSModule = mods.implementation.RobotWSModule
SenderModule = mods.implementation.SenderModule
SqliteModule = mods.implementation.SqliteModule
ProcessorModule = mods.implementation.ProcessorModule
WebInterfaceModule = mods.implementation.WebInterfaceModule
UnrealCarModule = mods.implementation.UnrealCarModule
YoloModule = mods.implementation.YoloModule
BaseModule = mods.base.BaseModule

ControlForRoverModule = mods.implementation.ControlForRoverModule
JoystickControlModule = mods.implementation.JoystickControllerModule


mm = ManagerModule(web_interface=False, port=8001)

# Модули
robot = RobotIOModule(
    name="RobotWS",
    manager=mm,
    receivers={
        "robot.telemetry": {
            "names": ["ClientIO", "ControlForRoverModule"],
            "modules": []
        },
        "robot.video": {
            "names": ["ClientIO"],
            "modules": []
        },
        "robot.connected": {
            "names": ["ClientIO"],
            "modules": []
        },
        "robot.disconnected": {
            "names": ["ClientIO"],
            "modules": []
        },
    },
    host="0.0.0.0",
    port=5000,
)

client = ClientIOModule(
    name="ClientIO",
    manager=mm,
    receivers={
        "robot.command": {
            "names": ["RobotWS"],
            "modules": []
        },
    },
    host="0.0.0.0",
    port=9002,
    static_dir=str(_ROOT / "src" / "modules" / "implementation" / "client_module" / "static" / "dist")
)

control_for_rover = ControlForRoverModule(
    name="ControlForRoverModule",
    manager=mm,
    receivers={
        "robot.command": {
            "names": ["RobotWS"],
            "modules": []
        }
    }
)

joystick_control = JoystickControlModule(
    name="JoystickControl",
    manager=mm,
    receivers={
        "joystick.command": {
            "names": ["ControlForRoverModule"],
            "modules": []
        },
    }
)

# log = ConsoleLogModule(name="ConsoleLog", manager=mm)

mm.connect_all_modules()
mm.start_all_threads()