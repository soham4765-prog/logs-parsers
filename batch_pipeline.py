import os
import sys
import time
import argparse
from pathlib import Path

# Explicit imports tailored to your app/parsers structure
from app.parsers.factory import LogParserFactory
from app.parsers.normalizer import NormalizationEngine

# Supported flight controller log extensions
SUPPORTED_EXTENSIONS = {".bin", ".ulg", ".bfl", ".bbl"}


def process_single_log(file_path: Path, output_dir: Path, target_freq_hz: int = 50) -> bool:
    """
    Parses a single flight log file and saves .uts.parquet and .uts.csv files into output_dir.
    """
    try:
        # 1. Instantiate the parser using Factory
        parser = LogParserFactory.get_parser(str(file_path))
        fc_type = parser.get_fc_type()

        # 2. Extract raw telemetry records
        raw_df = parser.extract_raw_df(str(file_path))
        if raw_df is None or raw_df.empty:
            print(f"  [⚠️ WARNING] Skipped {file_path.name}: No records extracted.")
            return False

        # 3. Normalize to UTS @ target frequency (default 50 Hz)
        uts_df = NormalizationEngine.normalize_to_uts(raw_df, target_freq_hz=target_freq_hz)

        # 4. Construct output file paths
        base_name = file_path.stem  # File name without extension
        parquet_out = output_dir / f"{base_name}.uts.parquet"
        csv_out = output_dir / f"{base_name}.uts.csv"

        # 5. Export files
        uts_df.to_parquet(parquet_out, engine="pyarrow", compression="snappy")
        uts_df.to_csv(csv_out, index=False)

        print(f"  [✅ SUCCESS] ({fc_type}) -> Saved: {parquet_out.name} ({len(uts_df):,} rows)")
        return True

    except Exception as err:
        print(f"  [❌ ERROR] Failed to process {file_path.name}: {err}")
        return False


def process_folder(input_dir_str: str, output_dir_str: str = None, target_freq_hz: int = 50):
    input_dir = Path(input_dir_str).resolve()

    if not input_dir.exists() or not input_dir.is_dir():
        print(f"[❌ ERROR] Directory not found: {input_dir}")
        return

    # Default output directory: outputs/ if output_dir_str isn't specified
    if output_dir_str:
        output_dir = Path(output_dir_str).resolve()
    else:
        output_dir = input_dir / "outputs"

    output_dir.mkdir(parents=True, exist_ok=True)

    # Gather supported log files (ignoring already processed .uts files)
    log_files = [
        f for f in input_dir.iterdir()
        if f.is_file() 
        and f.suffix.lower() in SUPPORTED_EXTENSIONS
        and not f.name.endswith(".uts.bin")  # Exclude generated output artifacts
    ]

    print("=" * 70)
    print(" 🚀 BATCH FLIGHT LOG CONVERTER")
    print(f" • Input Folder:  {input_dir}")
    print(f" • Output Folder: {output_dir}")
    print(f" • Target Frequency: {target_freq_hz} Hz")
    print(f" • Files Found:   {len(log_files)}")
    print("=" * 70)

    if not log_files:
        print(f"[⚠️ NOTICE] No supported log files ({', '.join(SUPPORTED_EXTENSIONS)}) found in folder.")
        return

    start_time = time.time()
    success_count = 0
    fail_count = 0

    for idx, file_path in enumerate(log_files, start=1):
        print(f"\n[{idx}/{len(log_files)}] Processing: {file_path.name}")
        is_success = process_single_log(file_path, output_dir, target_freq_hz)
        
        if is_success:
            success_count += 1
        else:
            fail_count += 1

    elapsed_time = time.time() - start_time

    print("\n" + "=" * 70)
    print(" 📊 BATCH PROCESSING SUMMARY")
    print(f" • Total Logs Scanned: {len(log_files)}")
    print(f" • Successfully Converted: {success_count}")
    print(f" • Failed / Skipped:     {fail_count}")
    print(f" • Total Time Elapsed:   {elapsed_time:.2f} seconds")
    print(f" • Output Directory:     {output_dir}")
    print("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch convert flight log files to UTS CSV & Parquet formats.")
    
    parser.add_argument(
        "input_folder",
        type=str,
        help="Path to the folder containing log files."
    )
    parser.add_argument(
        "-o", "--output_folder",
        type=str,
        default=None,
        help="Path to output folder (default: input_folder/outputs)."
    )
    parser.add_argument(
        "-f", "--freq",
        type=int,
        default=50,
        help="Target resampling frequency in Hz (default: 50)."
    )

    args = parser.parse_args()
    process_folder(args.input_folder, args.output_folder, args.freq)