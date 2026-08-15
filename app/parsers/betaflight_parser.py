# app/parsers/betaflight_parser.py
import pandas as pd
from orangebox import Parser as OrangeboxParser
from app.parsers.base_parser import BaseParser

class BetaflightParser(BaseParser):
    def get_fc_type(self) -> str:
        return "Betaflight"

    def extract_raw_df(self, file_path: str) -> pd.DataFrame:
        # 1. Load and read the .bfl / .bbl file directly in Python using orangebox
        try:
            parser = OrangeboxParser.load(file_path)
        except Exception as e:
            raise RuntimeError(f"Failed to read Betaflight log '{file_path}': {str(e)}")

        records = []

        # 2. Iterate through frame by frame directly from the binary stream
        for frame in parser.frames():
            data = frame.data
            record = {}
            
            # Timestamp in seconds
            if 'time' in data:
                record['timestamp_sec'] = data['time'] / 1e6
            elif 'loopIteration' in data:
                record['timestamp_sec'] = data['loopIteration'] * 0.000125  # approx looptime

            # Gyro scope rates
            record['gyro_x'] = data.get('gyroADC[0]', None)
            record['gyro_y'] = data.get('gyroADC[1]', None)
            record['gyro_z'] = data.get('gyroADC[2]', None)

            # Accelerometer
            record['accel_x'] = data.get('accSmooth[0]', None)
            record['accel_y'] = data.get('accSmooth[1]', None)
            record['accel_z'] = data.get('accel_z', None)

            # Battery
            record['vbat'] = data.get('vbatLatest', None)
            record['ibat'] = data.get('amperage', None)

            # Motors
            for i in range(4):
                if f'motor[{i}]' in data:
                    record[f'motor_{i+1}'] = data[f'motor[{i}]'] / 2047.0

            records.append(record)

        if not records:
            raise ValueError(f"No frames extracted from Betaflight file: {file_path}")

        return pd.DataFrame(records)