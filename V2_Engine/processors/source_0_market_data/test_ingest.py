"""
Test Runner — Validates the H10 Ingestor against real CSV data.

Usage:
    python -m V2_Engine.processors.source_0_market_data.test_ingest
    (run from the project root: 008-Auto-Pilot/)
"""

import os
import sys
import glob

# Ensure project root is on the path
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from V2_Engine.processors.source_0_market_data.h10_ingestor import H10Ingestor
from V2_Engine.config import V1_DATA_SAMPLE, V2_DATABASE_DIR


OUTPUT_FILE = os.path.join(V2_DATABASE_DIR, "debug_source0_h10.csv")


def find_csv_files(search_root: str) -> list[str]:
    """Recursively find all CSV files under search_root."""
    return sorted(glob.glob(os.path.join(search_root, "**", "*.csv"), recursive=True))


def main():
    print("=" * 60)
    print("  Source 0 — H10 Ingestor Test Run")
    print("=" * 60)

    # --- Step 1: Find CSV files ---
    print(f"\n[1/4] Searching for CSV files in V1_Legacy/data_sample/ ...")
    csv_files = find_csv_files(V1_DATA_SAMPLE)

    if not csv_files:
        print("  [FAIL] No CSV files found. Check V1_Legacy/data_sample/.")
        return

    print(f"      Found {len(csv_files)} CSV file(s):")
    for f in csv_files:
        print(f"        - {os.path.basename(f)}")

    # --- Step 2: Instantiate and run ingestor ---
    print(f"\n[2/4] Running H10Ingestor.ingest() ...")
    ingestor = H10Ingestor()
    df = ingestor.ingest(csv_files)

    # --- Step 3: Print diagnostics ---
    print(f"\n[3/4] Diagnostics:")
    print(f"      Date detected : {ingestor.date_str}")
    print(f"      Week number   : {ingestor.week_number}")
    print(f"      Files ingested: {len(ingestor.file_info)}")
    for info in ingestor.file_info:
        print(f"        - {info['filename']}: {info['rows']} rows, {info['columns']} cols")

    print(f"\n      Combined shape : {df.shape[0]} rows x {df.shape[1]} cols")

    if ingestor.ads is not None:
        print(f"      Ads rows       : {len(ingestor.ads)}")
    if ingestor.organic is not None:
        print(f"      Organic rows   : {len(ingestor.organic)}")

    # Show columns
    print(f"\n      Columns ({len(df.columns)}):")
    for col in df.columns:
        print(f"        - {col}  (dtype: {df[col].dtype})")

    # df.head()
    priority = ingestor.important_columns(df)
    display_cols = priority if priority else list(df.columns[:8])
    print(f"\n      df.head(5) — priority columns:")
    print(df[display_cols].head(5).to_string(index=False))

    # df.info() equivalent
    print(f"\n      Non-null counts:")
    for col in df.columns:
        non_null = df[col].notna().sum()
        print(f"        {col:40s}  {non_null:>5d} / {len(df)} non-null")

    # --- Step 4: Save ---
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")
    print(f"\n[4/4] Saved cleaned data to:\n      {OUTPUT_FILE}")

    print("\n" + "=" * 60)
    print("  DONE. Source 0 ingestor is operational.")
    print("=" * 60)


if __name__ == "__main__":
    main()
