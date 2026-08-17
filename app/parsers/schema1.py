# app/parsers/schema1.py
from typing import List

# Target standard columns required in the Universal Telemetry Schema (UTS)
UTS_STANDARD_COLUMNS: List[str] = [
    "time_sec",

    # Attitude (deg)
    "roll",
    "pitch",
    "yaw",

    # Desired attitude (deg)
    "roll_des",
    "pitch_des",
    "yaw_des",

    # Gyroscope (deg/s)
    "gyro_x",
    "gyro_y",
    "gyro_z",

    # Accelerometer (m/s^2 or g)
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

    # Motors (0.0 to 1.0 normalized)
    "motor_1",
    "motor_2",
    "motor_3",
    "motor_4",

    # Flight mode
    "flight_mode",
]