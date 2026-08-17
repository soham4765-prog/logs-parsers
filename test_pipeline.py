import os
import sys
import glob
from pathlib import Path
import pandas as pd

# ---------------------------------------------------------------------------
# Path Handling & Module Imports
# ---------------------------------------------------------------------------
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

# Also add parent directory to handle app.parsers imports
PARENT_DIR = CURRENT_DIR.parent.parent if CURRENT_DIR.name == "parsers" else CURRENT_DIR
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

try:
    from app.parsers.factory import LogParserFactory
    from app.parsers.normalizer import NormalizationEngine
    from app.parsers.schema1 import UTS_STANDARD_COLUMNS
    import app.parsers.uts_schema
except ImportError:
    try:
        from app.parsers.factory import LogParserFactory
        from app.parsers.normalizer import NormalizationEngine
        from app.parsers.schema1 import UTS_STANDARD_COLUMNS
        import app.parsers.uts_schema
    except ImportError as e:
        raise ImportError(f"Failed to import parser modules: {e}")


# ---------------------------------------------------------------------------
# Core Flight Log Processor
# ---------------------------------------------------------------------------
def process_flight_log(file_path: str, output_dir: str = None) -> bool:
    file_path = os.path.abspath(file_path)
    base_name = Path(file_path).name

    print("=" * 65)
    print("[*] UNIVERSAL TELEMETRY PARSER PIPELINE")
    print(f"[*] Target File: {base_name}")
    print(f"[*] Schema Standard: {len(UTS_STANDARD_COLUMNS)} columns (Strict schema1.py)")
    print("=" * 65)

    # 1. Check if input file exists
    if not os.path.exists(file_path):
        print(f"[❌ ERROR] File not found at path: {file_path}")
        return False

    # 2. Dynamically select parser based on file extension
    try:
        parser = LogParserFactory.get_parser(file_path)
        print(f"[+] Detected Flight Controller Type: {parser.get_fc_type()}")
    except ValueError as err:
        print(f"[❌ ERROR] {err}")
        return False

    # 3. Extract raw telemetry records
    print(f"[*] Extracting raw records using {parser.get_fc_type()} parser...")
    try:
        raw_df = parser.extract_raw_df(file_path)
        print(f"[+] Raw Extraction Complete: {len(raw_df):,} records extracted.")
    except Exception as err:
        print(f"[❌ ERROR] Failed during raw extraction: {err}")
        return False

    # 4. Normalize and resample to 50 Hz UTS grid (Ordered strictly to schema1.py)
    print("[*] Resampling & Normalizing to UTS @ 50 Hz...")
    try:
        uts_df = NormalizationEngine.normalize_to_uts(raw_df, target_freq_hz=50)
        print(f"[+] Normalization Complete: {len(uts_df):,} samples generated.")
    except Exception as err:
        print(f"[❌ ERROR] Failed during normalization: {err}")
        return False

    # 5. Display Preview
    print("\n📊 UTS Telemetry Sample (First 5 Rows):")
    print("-" * 65)
    preview_cols = [c for c in ["time_sec", "roll", "pitch", "yaw", "vbat", "motor_1"] if c in uts_df.columns]
    print(uts_df[preview_cols].head())
    print("-" * 65)

    # 6. Determine output paths and export
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        parquet_out = os.path.join(output_dir, f"{base_name}.uts.parquet")
        csv_out = os.path.join(output_dir, f"{base_name}.uts.csv")
    else:
        parquet_out = file_path + ".uts.parquet"
        csv_out = file_path + ".uts.csv"

    uts_df.to_parquet(parquet_out, engine="pyarrow", compression="snappy")
    uts_df.to_csv(csv_out, index=False)

    print("\n💾 Saved Outputs:")
    print(f"   • Parquet (For Analytics Engine): {parquet_out}")
    print(f"   • CSV     (For Human Inspection): {csv_out}")
    print(f"\n✅ Successfully converted '{base_name}' to UTS standard.")
    return True


# ---------------------------------------------------------------------------
# Entrypoint: Supports Single File OR Directory Batch Mode
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # If path provided via CLI: python test_pipeline.py <path_to_file_or_dir>
    if len(sys.argv) > 1:
        target_path = sys.argv[1]
    else:
        # Default fallback test path
        target_path = r"D:\logs parser\tests\2 01-01-1980 05-30-00.bin"

    if os.path.isdir(target_path):
        supported_exts = ["*.bin", "*.bfl", "*.bbl", "*.ulg", "*.csv"]
        found_files = []
        for ext in supported_exts:
            found_files.extend(glob.glob(os.path.join(target_path, ext)))

        target_files = [
            f for f in found_files 
            if not f.endswith(".uts.csv") and not f.endswith(".uts.parquet")
        ]

        print(f"[*] Found {len(target_files)} flight logs to convert in: {target_path}")
        for idx, f in enumerate(target_files, 1):
            print(f"\n[{idx}/{len(target_files)}]")
            process_flight_log(f)
    else:
        process_flight_log(target_path)