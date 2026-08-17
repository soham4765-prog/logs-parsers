# app/parsers/betaflight_parser.py
import numpy as np
import pandas as pd
from app.parsers.base_parser import BaseParser


class BetaflightParser(BaseParser):
    def get_fc_type(self) -> str:
        return "Betaflight"

    def extract_raw_df(self, file_path: str) -> pd.DataFrame:
        if file_path.lower().endswith(".csv"):
            return self._extract_from_csv(file_path)
        else:
            return self._extract_from_binary(file_path)

    def _extract_from_csv(self, file_path: str) -> pd.DataFrame:
        # Find header index to skip metadata rows
        skip = 0
        with open(file_path, "r", errors="ignore") as f:
            for i, line in enumerate(f):
                if '"loopIteration"' in line or line.startswith("loopIteration") or ('"axisP[0]"' in line):
                    skip = i
                    break

        df_raw = pd.read_csv(file_path, skiprows=skip, low_memory=False, on_bad_lines="skip")
        df_raw.columns = df_raw.columns.str.strip().str.replace('"', "")

        t_raw = pd.to_numeric(df_raw["time"], errors="coerce").fillna(0)
        timestamp_sec = t_raw / 1e6

        # Attitude & desired attitude
        heading_0 = pd.to_numeric(df_raw.get("heading[0]"), errors="coerce")
        heading_1 = pd.to_numeric(df_raw.get("heading[1]"), errors="coerce")
        heading_2 = pd.to_numeric(df_raw.get("heading[2]"), errors="coerce")
        err_0 = pd.to_numeric(df_raw.get("axisError[0]"), errors="coerce")
        err_1 = pd.to_numeric(df_raw.get("axisError[1]"), errors="coerce")
        err_2 = pd.to_numeric(df_raw.get("axisError[2]"), errors="coerce")

        roll = np.rad2deg(heading_0) if heading_0 is not None else np.nan
        pitch = np.rad2deg(heading_1) if heading_1 is not None else np.nan
        yaw = np.rad2deg(heading_2) if heading_2 is not None else np.nan

        roll_des = roll + err_0 if (roll is not None and err_0 is not None) else np.nan
        pitch_des = pitch + err_1 if (pitch is not None and err_1 is not None) else np.nan
        yaw_des = yaw + err_2 if (yaw is not None and err_2 is not None) else np.nan

        # Motors (158 to 2047 DShot range)
        motor_min, motor_max = 158.0, 2047.0
        m1 = (pd.to_numeric(df_raw.get("motor[0]"), errors="coerce") - motor_min) / (motor_max - motor_min)
        m2 = (pd.to_numeric(df_raw.get("motor[1]"), errors="coerce") - motor_min) / (motor_max - motor_min)
        m3 = (pd.to_numeric(df_raw.get("motor[2]"), errors="coerce") - motor_min) / (motor_max - motor_min)
        m4 = (pd.to_numeric(df_raw.get("motor[3]"), errors="coerce") - motor_min) / (motor_max - motor_min)

        # Accelerometer (2048 LSB = 1G = 9.80665 m/s^2)
        acc_scale = 9.80665 / 2048.0
        acc_x = pd.to_numeric(df_raw.get("accSmooth[0]"), errors="coerce") * acc_scale
        acc_y = pd.to_numeric(df_raw.get("accSmooth[1]"), errors="coerce") * acc_scale
        acc_z = pd.to_numeric(df_raw.get("accSmooth[2]"), errors="coerce") * acc_scale

        return pd.DataFrame({
            "timestamp_sec": timestamp_sec,
            "roll": roll, "pitch": pitch, "yaw": yaw,
            "roll_des": roll_des, "pitch_des": pitch_des, "yaw_des": yaw_des,
            "gyro_x": pd.to_numeric(df_raw.get("gyroADC[0]"), errors="coerce"),
            "gyro_y": pd.to_numeric(df_raw.get("gyroADC[1]"), errors="coerce"),
            "gyro_z": pd.to_numeric(df_raw.get("gyroADC[2]"), errors="coerce"),
            "accel_x": acc_x, "accel_y": acc_y, "accel_z": acc_z,
            "vbat": pd.to_numeric(df_raw.get("vbatLatest"), errors="coerce") / 100.0,
            "ibat": pd.to_numeric(df_raw.get("amperageLatest"), errors="coerce") / 100.0,
            "motor_1": m1.clip(0.0, 1.0), "motor_2": m2.clip(0.0, 1.0),
            "motor_3": m3.clip(0.0, 1.0), "motor_4": m4.clip(0.0, 1.0),
            "flight_mode": "ACRO"
        })

    def _extract_from_binary(self, file_path: str) -> pd.DataFrame:
        from orangebox import Parser as OrangeboxParser
        parser = OrangeboxParser.load(file_path)
        records = []

        for frame in parser.frames():
            d = frame.data
            t = d.get("time", 0) / 1e6
            records.append({
                "timestamp_sec": t,
                "gyro_x": d.get("gyroADC[0]"),
                "gyro_y": d.get("gyroADC[1]"),
                "gyro_z": d.get("gyroADC[2]"),
                "accel_x": d.get("accSmooth[0]", 0) * (9.80665 / 2048.0) if "accSmooth[0]" in d else None,
                "accel_y": d.get("accSmooth[1]", 0) * (9.80665 / 2048.0) if "accSmooth[1]" in d else None,
                "accel_z": d.get("accSmooth[2]", 0) * (9.80665 / 2048.0) if "accSmooth[2]" in d else None,
                "vbat": d.get("vbatLatest", 0) / 100.0 if "vbatLatest" in d else None,
                "ibat": d.get("amperage", 0) / 100.0 if "amperage" in d else None,
                "motor_1": max(0.0, min(1.0, (d.get("motor[0]", 158) - 158) / (2047 - 158))),
                "motor_2": max(0.0, min(1.0, (d.get("motor[1]", 158) - 158) / (2047 - 158))),
                "motor_3": max(0.0, min(1.0, (d.get("motor[2]", 158) - 158) / (2047 - 158))),
                "motor_4": max(0.0, min(1.0, (d.get("motor[3]", 158) - 158) / (2047 - 158))),
                "flight_mode": "ACRO"
            })
        return pd.DataFrame(records)