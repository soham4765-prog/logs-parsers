# app/parsers/uts_schema.py
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

try:
    from app.parsers.schema1 import UTS_STANDARD_COLUMNS
except ImportError:
    from schema1 import UTS_STANDARD_COLUMNS


@dataclass
class FieldSpec:
    name: str
    unit: str
    category: str
    description: str
    normal_range: Optional[tuple] = None
    required: bool = True


UTS_FIELDS = [
    FieldSpec("time_sec", "s", "core", "Sample timestamp, seconds since log start"),
    FieldSpec("roll", "deg", "attitude", "Actual roll angle"),
    FieldSpec("pitch", "deg", "attitude", "Actual pitch angle"),
    FieldSpec("yaw", "deg", "attitude", "Actual yaw angle (0-360 deg)"),
    FieldSpec("roll_des", "deg", "attitude", "Commanded/desired roll angle"),
    FieldSpec("pitch_des", "deg", "attitude", "Commanded/desired pitch angle"),
    FieldSpec("yaw_des", "deg", "attitude", "Commanded/desired yaw angle"),
    FieldSpec("gyro_x", "deg/s", "imu", "Gyroscope X (roll rate)", required=False),
    FieldSpec("gyro_y", "deg/s", "imu", "Gyroscope Y (pitch rate)", required=False),
    FieldSpec("gyro_z", "deg/s", "imu", "Gyroscope Z (yaw rate)", required=False),
    FieldSpec("accel_x", "m/s^2", "imu", "Accelerometer X", required=False),
    FieldSpec("accel_y", "m/s^2", "imu", "Accelerometer Y", required=False),
    FieldSpec("accel_z", "m/s^2", "imu", "Accelerometer Z", required=False),
    FieldSpec("vbat", "V", "battery", "Battery voltage", normal_range=(3.3, 4.35), required=False),
    FieldSpec("ibat", "A", "battery", "Battery current draw", required=False),
    FieldSpec("lat", "deg", "gps", "GPS latitude", required=False),
    FieldSpec("lon", "deg", "gps", "GPS longitude", required=False),
    FieldSpec("alt", "m", "gps", "Altitude", required=False),
    FieldSpec("motor_1", "0-1 normalized", "motor", "Motor 1 output"),
    FieldSpec("motor_2", "0-1 normalized", "motor", "Motor 2 output"),
    FieldSpec("motor_3", "0-1 normalized", "motor", "Motor 3 output"),
    FieldSpec("motor_4", "0-1 normalized", "motor", "Motor 4 output"),
    FieldSpec("flight_mode", "string/enum", "core", "Flight controller mode"),
]

UTS_FIELD_NAMES = [f.name for f in UTS_FIELDS]

# Strict drift prevention assertion
assert UTS_FIELD_NAMES == UTS_STANDARD_COLUMNS, (
    "uts_schema.py's UTS_FIELDS has drifted out of sync with schema1.py's "
    "UTS_STANDARD_COLUMNS -- these must always name/order the same columns.\n"
    f"uts_schema: {UTS_FIELD_NAMES}\nschema1.py:  {UTS_STANDARD_COLUMNS}"
)

MOTOR_COLUMNS = ["motor_1", "motor_2", "motor_3", "motor_4"]

THRESHOLDS: Dict[str, Dict[str, float]] = {
    "roll_rmse_deg": {"good": 3.5, "warn": 7.0, "bad": 12.0},
    "pitch_rmse_deg": {"good": 3.5, "warn": 7.0, "bad": 12.0},
    "yaw_rmse_deg": {"good": 5.0, "warn": 10.0, "bad": 15.0},
    "motor_imbalance": {"good": 0.15, "warn": 0.30, "bad": 0.45},
    "battery_sag_per_cell_v": {"good": 0.30, "warn": 0.50, "bad": 0.70},
    "vibration_rms_total": {"good": 15.0, "warn": 30.0, "bad": 45.0},
    "dominant_fft_freq_hz": {"good": 20.0, "warn": 60.0, "bad": 120.0},
}