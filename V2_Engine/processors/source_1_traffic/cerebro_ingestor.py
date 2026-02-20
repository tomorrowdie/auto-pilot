"""
Cerebro Ingestor — ETL pipeline for Helium 10 Cerebro keyword data.

Reads raw Cerebro CSV, cleans and normalizes all columns,
enriches with derived fields, and saves to Parquet + debug CSV.

Usage:
    python -m V2_Engine.processors.source_1_traffic.cerebro_ingestor
"""

import os

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Paths (dynamic, no hardcoded absolutes)
# ---------------------------------------------------------------------------
_BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )
    )
)
_RAW_DIR = os.path.join(_BASE_DIR, "data", "raw", "source_1_market")
_PROCESSED_DIR = os.path.join(_BASE_DIR, "data", "processed")
_RAW_FILENAME = "US_AMAZON_cerebro__2026-02-08.csv"

# ---------------------------------------------------------------------------
# Column mapping: raw header -> snake_case
# ---------------------------------------------------------------------------
_COLUMN_MAP = {
    "Keyword Phrase": "keyword_phrase",
    "ABA Total Click Share": "aba_total_click_share",
    "ABA Total Conv. Share": "aba_total_conv_share",
    "Keyword Sales": "keyword_sales",
    "Cerebro IQ Score": "cerebro_iq_score",
    "Search Volume": "search_volume",
    "Search Volume Trend": "search_volume_trend",
    "H10 PPC Sugg. Bid": "h10_ppc_sugg_bid",
    "H10 PPC Sugg. Min Bid": "h10_ppc_sugg_min_bid",
    "H10 PPC Sugg. Max Bid": "h10_ppc_sugg_max_bid",
    "Sponsored ASINs": "sponsored_asins",
    "Competing Products": "competing_products",
    "CPR": "cpr",
    "Organic": "organic",
    "Title Density": "title_density",
    "Smart Complete": "smart_complete",
    "Amazon Recommended": "amazon_recommended",
}

# All columns that must be numeric after cleaning
_NUMERIC_COLS = [
    "aba_total_click_share",
    "aba_total_conv_share",
    "keyword_sales",
    "cerebro_iq_score",
    "search_volume",
    "search_volume_trend",
    "h10_ppc_sugg_bid",
    "h10_ppc_sugg_min_bid",
    "h10_ppc_sugg_max_bid",
    "sponsored_asins",
    "competing_products",
    "cpr",
    "organic",
    "title_density",
    "smart_complete",
    "amazon_recommended",
]

# Subset that should be int (not float) after fillna(0)
_INT_COLS = [
    "keyword_sales",
    "cerebro_iq_score",
    "search_volume",
    "search_volume_trend",
    "sponsored_asins",
    "competing_products",
    "cpr",
    "organic",
    "title_density",
    "smart_complete",
    "amazon_recommended",
]


# ---------------------------------------------------------------------------
# Cleaning helpers
# ---------------------------------------------------------------------------

def _clean_numeric_value(val):
    """Strip commas, '>', '$', '%' and convert '-'/'n/a'/empty to NaN."""
    if pd.isna(val):
        return np.nan
    s = str(val).strip()
    if s in ("-", "n/a", "N/A", ""):
        return np.nan
    s = s.replace(",", "").replace(">", "").replace("$", "").replace("%", "")
    try:
        return float(s)
    except ValueError:
        return np.nan


# ---------------------------------------------------------------------------
# Main ETL function
# ---------------------------------------------------------------------------

def ingest_cerebro_data(csv_path: str | None = None) -> pd.DataFrame:
    """
    Full ETL pipeline for Cerebro keyword data.

    1. Read raw CSV
    2. Rename columns to snake_case
    3. Clean all numeric columns (strip symbols, coerce types)
    4. Fill NaN with 0
    5. Add word_count column
    6. Save Parquet + debug CSV

    Args:
        csv_path: Optional override path to the raw CSV.
                  Defaults to data/raw/source_1_market/US_AMAZON_cerebro__2026-02-08.csv

    Returns:
        Cleaned pandas DataFrame.
    """
    if csv_path is None:
        csv_path = os.path.join(_RAW_DIR, _RAW_FILENAME)

    print(f"[Cerebro Ingestor] Reading: {csv_path}")
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    print(f"[Cerebro Ingestor] Raw shape: {df.shape[0]} rows x {df.shape[1]} cols")

    # --- Rename to snake_case ---
    df = df.rename(columns=_COLUMN_MAP)

    # --- Clean numeric columns ---
    for col in _NUMERIC_COLS:
        if col in df.columns:
            df[col] = df[col].apply(_clean_numeric_value)
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df[col] = df[col].fillna(0)

    # --- Cast integer columns ---
    for col in _INT_COLS:
        if col in df.columns:
            df[col] = df[col].astype(int)

    # --- Enrich: word_count ---
    df["word_count"] = (
        df["keyword_phrase"].str.split().str.len().fillna(0).astype(int)
    )

    # --- Save outputs ---
    os.makedirs(_PROCESSED_DIR, exist_ok=True)

    parquet_path = os.path.join(_PROCESSED_DIR, "source_1_cerebro.parquet")
    df.to_parquet(parquet_path, index=False)
    print(f"[Cerebro Ingestor] Saved Parquet: {parquet_path}")

    debug_path = os.path.join(_PROCESSED_DIR, "source_1_debug.csv")
    df.head(50).to_csv(debug_path, index=False)
    print(f"[Cerebro Ingestor] Saved debug CSV: {debug_path} (first 50 rows)")

    print(f"[Cerebro Ingestor] Done. Final shape: {df.shape[0]} rows x {df.shape[1]} cols")
    return df


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    result = ingest_cerebro_data()

    print("\n--- Word Count Verification (first 3 rows) ---")
    print(result[["keyword_phrase", "word_count"]].head(3).to_string(index=False))

    print("\n--- Data Types ---")
    print(result.dtypes.to_string())
