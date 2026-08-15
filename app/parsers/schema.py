from typing import List


# Target standard columns required in the Universal Telemetry Schema (UTS)

UTS_STANDARD_COLUMNS: List[str] = [
    "time_sec",

    # Attitude
    "roll",
    "pitch",
    "yaw",

    # Desired attitude
    "roll_des",
    "pitch_des",
    "yaw_des",

    # Gyroscope
    "gyro_x",
    "gyro_y",
    "gyro_z",

    # Accelerometer
    "accel_x",
    "accel_y",
    "accel_z",

    # Battery
    "vbat",
    "ibat",

    # GPS / Position
    "lat",
    "lon",
    "alt",

    # Motors
    "motor_1",
    "motor_2",
    "motor_3",
    "motor_4",

    # Flight mode
    "flight_mode",
]