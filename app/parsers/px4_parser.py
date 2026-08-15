import pandas as pd
import numpy as np
from pyulog import ULog

from app.parsers.base_parser import BaseParser


class PX4Parser(BaseParser):

    def get_fc_type(self) -> str:
        return "PX4"

    def extract_raw_df(self, file_path: str) -> pd.DataFrame:
        ulog = ULog(file_path)

        extracted_dfs = []

        # 1. Extract Attitude Data
        try:
            att = ulog.get_dataset("vehicle_attitude").data

            df_att = pd.DataFrame({
                "timestamp": att["timestamp"],
                "roll": np.degrees(att["roll"]),
                "pitch": np.degrees(att["pitch"]),
                "yaw": np.degrees(att["yaw"])
            })

            extracted_dfs.append(df_att)

        except (KeyError, ValueError):
            pass

        # 2. Extract Sensor Data
        try:
            sensor = ulog.get_dataset("sensor_combined").data

            df_sensor = pd.DataFrame({
                "timestamp": sensor["timestamp"],
                "gyro_x": np.degrees(sensor["gyro_rad[0]"]),
                "gyro_y": np.degrees(sensor["gyro_rad[1]"]),
                "gyro_z": np.degrees(sensor["gyro_rad[2]"]),
                "accel_x": sensor["accelerometer_m_s2[0]"],
                "accel_y": sensor["accelerometer_m_s2[1]"],
                "accel_z": sensor["accelerometer_m_s2[2]"]
            })

            extracted_dfs.append(df_sensor)

        except (KeyError, ValueError):
            pass

        # 3. Extract Battery Data
        try:
            bat = ulog.get_dataset("battery_status").data

            df_bat = pd.DataFrame({
                "timestamp": bat["timestamp"],
                "vbat": bat["voltage_v"],
                "ibat": bat["current_a"]
            })

            extracted_dfs.append(df_bat)

        except (KeyError, ValueError):
            pass

        # Check if anything was extracted
        if not extracted_dfs:
            raise ValueError(
                "Failed to extract any valid ULog topics from file."
            )

        # Merge extracted topics
        raw_df = extracted_dfs[0]

        for df in extracted_dfs[1:]:
            raw_df = pd.merge_ordered(
                raw_df,
                df,
                on="timestamp",
                how="outer"
            )

        # Convert microseconds to seconds
        raw_df["timestamp_sec"] = raw_df["timestamp"] / 1e6

        return raw_df