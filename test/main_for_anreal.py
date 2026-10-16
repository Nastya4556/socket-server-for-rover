from src import modules as mods

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

PidControlForAnrealModule = mods.implementation.PidControlForAnrealModule

mm = ManagerModule()

ue_car = UnrealCarModule(name="UnrealCar", manager=mm,
                                     receivers={"raw_ue_data":
                                                    {"names": ["ConsoleLog", "PidControlForAnrealModule"
                                                               ]}
                                                })


log = ConsoleLogModule(name="ConsoleLog", manager=mm)


pid_control_for_anreal_module = PidControlForAnrealModule(name = "PidControlForAnrealModule", manager = mm,
                                                  receivers = {"robot.command":
                                                                   {"names": ["UnrealCar"
                                                                              ]}
                                                               })


mm.connect_all_modules()
mm.start_all_threads()


