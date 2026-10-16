from src import modules as mods, infinite_loop, NNPidControlForRoverModule, PidControlForAnrealModule

ManagerModule = mods.base.ManagerModule
CarModule = mods.implementation.CarModule
ClientIOModule = mods.implementation.ClientIOModule
ConsoleLogModule = mods.implementation.ConsoleLogModule
ControllerModule = mods.implementation.CarControllerModule
RobotIOModule = mods.implementation.RobotWSModule
SenderModule = mods.implementation.SenderModule
SqliteModule = mods.implementation.SqliteModule
ProcessorModule = mods.implementation.ProcessorModule
WebInterfaceModule = mods.implementation.WebInterfaceModule
UnrealCarModule = mods.implementation.UnrealCarModule
YoloModule = mods.implementation.YoloModule
BaseModule = mods.base.BaseModule

ControlForRoverModule = mods.implementation.ControlForRoverModule
NNControlForRoverModule = mods.implementation.NNControlForRoverModule
PidControlForAnrealModule = mods.implementation.PidControlForAnrealModule
NNPidControlForAnrealModule = mods.implementation.NNPidControlForAnrealModule

JoystickControlModule = mods.implementation.JoystickControllerModule


mm = ManagerModule()

# ue_car = UnrealCarModule(name="UnrealCar", manager=mm,
#                                      receivers={"raw_ue_data":
#                                                     {"names": ["ConsoleLog"]}
#                                                 })

log = ConsoleLogModule(name="ConsoleLog", manager=mm)

robot = RobotIOModule(
    name="RobotIO",
    manager=mm,
    receivers = {
        "robot.telemetry": {
            "names": ["ClientIO"],# ["ClientIO", "ConsoleLog"],
            "modules": []
        },
        "robot.connected": {
            "names": ["ClientIO"],
            "modules": []
        },
        "robot.disconnected": {
            "names": ["ClientIO"],
            "modules": []
        }
    },
    host="0.0.0.0",
    port=5000,
)

client = ClientIOModule(
    name="ClientIO",
    manager=mm,
    receivers = {
        "robot.telemetry": {
            "names": ["ControlForRover"], # "ConsoleLog"
            "modules": []
        },
    },
    host="0.0.0.0",
    port=8001,
    static_dir="static"
)


control_for_rover = ControlForRoverModule(name="ControlForRover", manager=mm,
                                                 receivers={
                                                     "robot.command":{
                                                        "names": ["ClientIO"]
                                                     }})

joystick_control = JoystickControlModule(name="JoystickControl", manager = mm,
                                         receivers={"joystick.command":
                                                        {"names": ["ControlForRover"]}
                                                    })



mm.connect_all_modules()
mm.start_all_threads()



