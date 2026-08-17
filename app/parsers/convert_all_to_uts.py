# convert_all_to_uts.py
import os
import glob
from pathlib import Path
from app.parsers.factory import LogParserFactory
from app.parsers.normalizer import NormalizationEngine
from app.parsers.schema1 import UTS_STANDARD_COLUMNS


def convert_file(file_path: str, output_dir: str = "outputs"):
    os.makedirs(output_dir, exist_ok=True)
    base_name = Path(file_path).name

    try:
        # 1. Select appropriate parser via Factory
        parser = LogParserFactory.get_parser(file_path)
        fc_type = parser.get_fc_type()
        print(f"[*] Processing {base_name} as {fc_type}...")

        # 2. Extract raw frame records
        raw_df = parser.extract_raw_df(file_path)

        # 3. Resample to 50 Hz & align to schema1 columns
        uts_df = NormalizationEngine.normalize_to_uts(raw_df, target_freq_hz=50)

        # 4. Save both CSV and Parquet
        csv_out = os.path.join(output_dir, f"{base_name}.uts.csv")
        parquet_out = os.path.join(output_dir, f"{base_name}.uts.parquet")

        uts_df.to_csv(csv_out, index=False)
        uts_df.to_parquet(parquet_out, engine="pyarrow", compression="snappy")

        print(f"  [+] Saved UTS CSV:     {csv_out}")
        print(f"  [+] Saved UTS Parquet: {parquet_out}")
        return True

    except Exception as e:
        print(f"  [!] Failed to convert {base_name}: {e}")
        return False


def convert_all(input_dir: str = "."):
    supported_extensions = ["*.bin", "*.bfl", "*.bbl", "*.ulg", "*.csv"]
    files_to_process = []

    for ext in supported_extensions:
        files_to_process.extend(glob.glob(os.path.join(input_dir, ext)))

    # Filter out already converted UTS files
    files_to_process = [f for f in files_to_process if not f.endswith(".uts.csv") and not f.endswith(".uts.parquet")]

    print("=" * 65)
    print(f"[*] UNIVERSAL UTS CONVERTER ENGINE")
    print(f"[*] Target Schema Columns ({len(UTS_STANDARD_COLUMNS)}): {UTS_STANDARD_COLUMNS}")
    print(f"[*] Found {len(files_to_process)} log files to convert.")
    print("=" * 65)

    success_count = 0
    for idx, f in enumerate(files_to_process, 1):
        if convert_file(f):
            success_count += 1

    print("\n" + "=" * 65)
    print(f"✅ Completed: {success_count}/{len(files_to_process)} files converted to UTS.")
    print("=" * 65)


if __name__ == "__main__":
    convert_all(input_dir=r"D:\eda")