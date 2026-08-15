import os
import sys
import pandas as pd

# Option A: Import relative if in the same folder
# Option B: Use app package imports if running from root directory
try:
    from app.parsers.factory import LogParserFactory
    from app.parsers.normalizer import NormalizationEngine
except ImportError:
    from app.parsers.factory import LogParserFactory
    from app.parsers.normalizer import NormalizationEngine


def process_flight_log(file_path: str):
    print("=" * 60)
    print(f"[*] UNIVERSAL TELEMETRY PARSER PIPELINE")
    print(f"[*] Target File: {file_path}")
    print("=" * 60)

    # 1. Check if the input log file actually exists
    if not os.path.exists(file_path):
        print(f"[❌ ERROR] File not found at path: {file_path}")
        return

    # 2. Dynamically pick parser based on file extension
    try:
        parser = LogParserFactory.get_parser(file_path)
        print(f"[+] Detected Flight Controller Type: {parser.get_fc_type()}")
    except ValueError as err:
        print(f"[❌ ERROR] {err}")
        return

    # 3. Extract raw telemetry records
    print(f"[*] Extracting raw records using {parser.get_fc_type()} parser...")
    try:
        raw_df = parser.extract_raw_df(file_path)
        print(f"[+] Raw Extraction Complete: {len(raw_df):,} raw records extracted.")
    except Exception as err:
        print(f"[❌ ERROR] Failed during raw extraction: {err}")
        return

    # 4. Normalize and resample to 50 Hz UTS grid
    print("[*] Resampling & Normalizing to UTS @ 50 Hz...")
    try:
        uts_df = NormalizationEngine.normalize_to_uts(raw_df, target_freq_hz=50)
        print(f"[+] Normalization Complete: {len(uts_df):,} samples generated.")
    except Exception as err:
        print(f"[❌ ERROR] Failed during normalization: {err}")
        return

    # 5. Display Preview
    print("\n📊 UTS Telemetry Sample (First 5 Rows):")
    print("-" * 60)
    preview_cols = [c for c in ["time_sec", "roll", "pitch", "yaw", "vbat", "motor_1"] if c in uts_df.columns]
    print(uts_df[preview_cols].head())
    print("-" * 60)

    # 6. Export outputs
    parquet_out = file_path + ".uts.parquet"
    csv_out = file_path + ".uts.csv"

    uts_df.to_parquet(parquet_out, engine='pyarrow', compression='snappy')
    uts_df.to_csv(csv_out, index=False)

    print(f"\n💾 Saved Outputs:")
    print(f"   • Parquet (For Analytics Engine): {parquet_out}")
    print(f"   • CSV     (For Human Inspection): {csv_out}")
    print("\n✅ Processing finished successfully!")


if __name__ == "__main__":
    # Support passing file path via command line: python test_pipeline.py <path_to_log>
    if len(sys.argv) > 1:
        target_file = sys.argv[1]
    else:
        # Default fallback test file
        target_file = r"app/parsers/109 01-01-1980 05-30-00.bin"

    process_flight_log(target_file)