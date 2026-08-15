import os
import sys
import pandas as pd

# Append current directory to path so app modules import cleanly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ardupilot_parser import ArduPilotParser
from normalizer import NormalizationEngine 

def run_parser(bin_file_path: str):
    print("=" * 60)
    print(f"[*] Starting ArduPilot Log Ingestion")
    print(f"[*] Target File: {bin_file_path}")
    print("=" * 60)

    # 1. Validate File Existence
    if not os.path.exists(bin_file_path):
        print(f"[ERROR] File not found: {bin_file_path}")
        return

    # 2. Extract Raw Telemetry Data using Pymavlink
    print("\n[Step 1/3] Parsing binary Dataflash messages (ATT, IMU, BAT, RCOU)...")
    parser = ArduPilotParser()
    try:
        raw_df = parser.extract_raw_df(bin_file_path)
        print(f"[SUCCESS] Extracted {len(raw_df):,} raw message records.")
    except Exception as e:
        print(f"[ERROR] Failed to extract raw records: {e}")
        return

    # 3. Normalize and Resample to 50 Hz UTS
    print("\n[Step 2/3] Resampling & normalizing to 50 Hz Universal Telemetry Schema (UTS)...")
    try:
        uts_df = NormalizationEngine.normalize_to_uts(raw_df, target_freq_hz=50)
        print(f"[SUCCESS] Generated UTS dataset with {len(uts_df):,} rows.")
    except Exception as e:
        print(f"[ERROR] Normalization failed: {e}")
        return

    # 4. Inspect Parsed Output
    print("\n[Step 3/3] Inspecting Normalized UTS Telemetry Data:")
    print("-" * 60)
    print(uts_df[["time_sec", "roll", "pitch", "yaw", "vbat", "motor_1"]].head(10))
    print("-" * 60)

    # Summary Statistics
    duration_sec = uts_df["time_sec"].max()
    print(f"\n📊 Flight Summary Stats:")
    print(f"   • Total Duration: {duration_sec:.2f} seconds ({duration_sec/60:.2f} minutes)")
    print(f"   • Max Voltage: {uts_df['vbat'].max()} V | Min Voltage: {uts_df['vbat'].min()} V")
    print(f"   • Max Roll Angle: {uts_df['roll'].max()}° | Min Roll Angle: {uts_df['roll'].min()}°")

    # 5. Export Datasets for Analytics & Debugging
    parquet_out = bin_file_path + ".uts.parquet"
    csv_out = bin_file_path + ".uts.csv"

    uts_df.to_parquet(parquet_out, engine="pyarrow", compression="snappy")
    uts_df.to_csv(csv_out, index=False)

    print(f"\n💾 Saved UTS Outputs:")
    print(f"   • Compressed Parquet (For Analytics Engine): {parquet_out}")
    print(f"   • CSV File (For Quick Inspection):           {csv_out}")
    print("\n✅ Parsing completed successfully!") 

if __name__ == "__main__":
    # ⚠️ Replace this with the actual path to your .bin log file!
    LOG_FILE_PATH = "4 01-01-1980 05-30-00.bin" 
    run_parser(LOG_FILE_PATH)