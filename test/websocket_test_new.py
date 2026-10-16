import time

from src import modules as mods


mm = mods.ManagerModule(web_interface=False, port=8001)

# modules
mm.create_module(
    "RobotIOModule",
    name="RobotWS",
    host="0.0.0.0",
    port=5000
)

mm.create_module(
    "ClientIOModule",
    name="ClientIO",
    host="0.0.0.0",
    port=9002,
    static_dir="../src/modules/implementation/client_module/static/dist"
)


# connections
mm.connect(
    sender_name="RobotWS",
    receiver_name="ClientIO",
    signature="robot.telemetry"
)

mm.connect(
    sender_name="RobotWS",
    receiver_name="ClientIO",
    signature="robot.video"
)

mm.connect(
    sender_name="RobotWS",
    receiver_name="ClientIO",
    signature="robot.connected"
)

mm.connect(
    sender_name="RobotWS",
    receiver_name="ClientIO",
    signature="robot.disconnected"
)

mm.connect(
    sender_name="ClientIO",
    receiver_name="RobotWS",
    signature="robot.command"
)



# mm.create_module(
#     "ConsoleLogModule",
#     name="ConsoleLog",
# )

# mm.connect(
#     sender_name="RobotWS",
#     receiver_name="ConsoleLog",
#     signature="robot.telemetry"
# )


# mm.create_module(
#     "YoloModule",
#     name="Yolo",
# )
#
# mm.connect(
#     sender_name="RobotWS",
#     receiver_name="Yolo",
#     signature="robot.video"
# )
# mm.connect(
#     sender_name="Yolo",
#     receiver_name="ClientIO",
#     signature="robot.video"
# )

mm.create_module("JoystickControllerModule",
                 name = "JoystickControl")

mm.create_module("PidControlForRoverModule",
                 name = "PidControlForRoverModule")

mm.connect(
    sender_name = "JoystickControl",
    receiver_name = "PidControlForRoverModule",
    signature = "joystick.command"
    )

mm.connect(
    sender_name="PidControlForRoverModule",
    receiver_name="RobotWS",
    signature="robot.command"
)
mm.connect(
    sender_name="RobotWS",
    receiver_name="PidControlForRoverModule",
    signature="robot.telemetry"
)


mm.start_all_threads()

