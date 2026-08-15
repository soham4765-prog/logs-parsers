import os

from app.parsers.factory import LogParserFactory
from app.parsers.normalizer import NormalizationEngine


OUTPUT_DIR = "outputs"

os.makedirs(OUTPUT_DIR, exist_ok=True)


def process_log(file_path: str):
    """
    Complete flight-log processing pipeline:

    Log file
        ↓
    Parser selection
        ↓
    Raw telemetry extraction
        ↓
    UTS normalization
        ↓
    Parquet output
    """

    print("=" * 60)
    print("[*] UNIVERSAL TELEMETRY PROCESSING PIPELINE")
    print(f"[*] Input File: {file_path}")
    print("=" * 60)

    # ---------------------------------------------------------
    # 1. Select the correct parser
    # ---------------------------------------------------------

    parser = LogParserFactory.get_parser(file_path)

    print(f"[*] Flight Controller: {parser.get_fc_type()}")
    print(f"[*] Parser: {parser.__class__.__name__}")

    # ---------------------------------------------------------
    # 2. Extract raw telemetry
    # ---------------------------------------------------------

    print("[*] Extracting raw telemetry...")

    raw_df = parser.extract_raw_df(file_path)

    print(f"[+] Raw records extracted: {len(raw_df)}")
    print(f"[+] Raw columns: {list(raw_df.columns)}")

    # ---------------------------------------------------------
    # 3. Normalize telemetry into UTS
    # ---------------------------------------------------------

    print("[*] Normalizing telemetry to UTS...")

    uts_df = NormalizationEngine.normalize_to_uts(
        raw_df,
        target_freq_hz=50
    )

    print(f"[+] UTS records: {len(uts_df)}")
    print(f"[+] UTS columns: {len(uts_df.columns)}")

    # ---------------------------------------------------------
    # 4. Create output filename
    # ---------------------------------------------------------

    input_filename = os.path.basename(file_path)

    filename_without_extension = os.path.splitext(
        input_filename
    )[0]

    output_filename = (
        filename_without_extension + ".uts.parquet"
    )

    output_path = os.path.join(
        OUTPUT_DIR,
        output_filename
    )

    # ---------------------------------------------------------
    # 5. Save Parquet
    # ---------------------------------------------------------

    print("[*] Saving UTS Parquet...")

    uts_df.to_parquet(
        output_path,
        index=False
    )

    print(f"[+] Output saved: {output_path}")
    print("=" * 60)
    print("[+] PIPELINE COMPLETE")
    print("=" * 60)

    return output_path