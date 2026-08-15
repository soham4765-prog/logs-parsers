import pandas as pd
from pymavlink import mavutil
from app.parsers.base_parser import BaseParser

class ArduPilotParser(BaseParser):
    def get_fc_type(self) -> str:
        return "ArduPilot"

    def extract_raw_df(self, file_path: str) -> pd.DataFrame:
        mlog = mavutil.mavlink_connection(file_path)
        
        records = []
        current_state = {}

        # Scan binary MAVLink / Dataflash log messages sequentially
        while True:
            msg = mlog.recv_msg()
            if msg is None:
                break
            
            msg_type = msg.get_type()
            
            if msg_type == 'ATT':
                current_state['timestamp_sec'] = getattr(msg, 'TimeUS', 0) / 1e6
                current_state['roll'] = getattr(msg, 'Roll', None)
                current_state['pitch'] = getattr(msg, 'Pitch', None)
                current_state['yaw'] = getattr(msg, 'Yaw', None)
                current_state['roll_des'] = getattr(msg, 'DesRoll', None)
                current_state['pitch_des'] = getattr(msg, 'DesPitch', None)
                current_state['yaw_des'] = getattr(msg, 'DesYaw', None)
                records.append(dict(current_state))
                
            elif msg_type == 'IMU':
                current_state['timestamp_sec'] = getattr(msg, 'TimeUS', 0) / 1e6
                current_state['gyro_x'] = getattr(msg, 'GxF', None)
                current_state['gyro_y'] = getattr(msg, 'GyF', None)
                current_state['gyro_z'] = getattr(msg, 'GzF', None)
                current_state['accel_x'] = getattr(msg, 'Ax', None)
                current_state['accel_y'] = getattr(msg, 'Ay', None)
                current_state['accel_z'] = getattr(msg, 'Az', None)
                records.append(dict(current_state))
                
            elif msg_type == 'BAT':
                current_state['timestamp_sec'] = getattr(msg, 'TimeUS', 0) / 1e6
                current_state['vbat'] = getattr(msg, 'Volt', None)
                current_state['ibat'] = getattr(msg, 'Curr', None)
                records.append(dict(current_state))
                
            elif msg_type == 'RCOU':
                current_state['timestamp_sec'] = getattr(msg, 'TimeUS', 0) / 1e6
                # Normalize PWM output (1000us - 2000us) to range 0.0 - 1.0
                c1 = getattr(msg, 'C1', 1000)
                c2 = getattr(msg, 'C2', 1000)
                c3 = getattr(msg, 'C3', 1000)
                c4 = getattr(msg, 'C4', 1000)
                current_state['motor_1'] = max(0.0, min(1.0, (c1 - 1000) / 1000.0))
                current_state['motor_2'] = max(0.0, min(1.0, (c2 - 1000) / 1000.0))
                current_state['motor_3'] = max(0.0, min(1.0, (c3 - 1000) / 1000.0))
                current_state['motor_4'] = max(0.0, min(1.0, (c4 - 1000) / 1000.0))
                records.append(dict(current_state))

            elif msg_type == 'MODE':
                current_state['flight_mode'] = str(getattr(msg, 'Mode', 'UNKNOWN'))

        if not records:
            raise ValueError("No valid ArduPilot dataflash records extracted from .BIN file.")

        return pd.DataFrame(records)