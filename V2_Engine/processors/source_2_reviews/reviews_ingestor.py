"""
Source 2 — Review Ingestor (Sorftime Excel → Clean Parquet).

Reads Sorftime-exported .xlsx files with Chinese column headers,
maps them to English snake_case, cleans types, and saves to Parquet.

Input:  data/raw/source_2_review/*.xlsx
Output: data/processed/source_2_reviews.parquet
        data/processed/source_2_reviews_debug.csv (first 50 rows)

Usage:
    # From dashboard (file object):
    from V2_Engine.processors.source_2_reviews.reviews_ingestor import ingest_reviews
    df = ingest_reviews(file_obj)

    # CLI batch mode:
    python -m V2_Engine.processors.source_2_reviews.reviews_ingestor
"""

from __future__ import annotations

import os
import glob
from io import BytesIO

import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
_RAW_DIR = os.path.join(_PROJECT_ROOT, "data", "raw", "source_2_review")
_PROCESSED_DIR = os.path.join(_PROJECT_ROOT, "data", "processed")
_PARQUET_FILE = os.path.join(_PROCESSED_DIR, "source_2_reviews.parquet")
_DEBUG_CSV = os.path.join(_PROCESSED_DIR, "source_2_reviews_debug.csv")

# ---------------------------------------------------------------------------
# Schema Contract — LOCKED for future PostgreSQL integration
# ---------------------------------------------------------------------------
CHINESE_TO_ENGLISH_MAP = {
    "ASIN": "asin",
    "\u8bc4\u8bba\u4eba": "reviewer_name",           # 评论人
    "\u8bc4\u8bba\u4eba\u6807\u8bb0": "reviewer_id",  # 评论人标记
    "\u662f\u5426vp": "is_verified_purchase",          # 是否vp
    "\u8bc4\u8bba\u65f6\u95f4": "review_date",        # 评论时间
    "\u6807\u9898": "review_title",                    # 标题
    "\u5185\u5bb9": "review_content",                  # 内容
    "\u53d8\u4f53\u5c5e\u6027": "variant",            # 变体属性
    "\u661f\u7ea7": "rating",                          # 星级
    "\u8d5e\u540c\u6570": "helpful_votes",             # 赞同数
    "\u7ad9\u70b9\u6765\u6e90": "marketplace",        # 站点来源
    "\u662f\u5426\u56fe\u7247": "has_image",           # 是否图片
    "\u662f\u5426\u6709\u89c6\u9891": "has_video",    # 是否有视频
    "\u94fe\u63a5": "review_link",                     # 链接
}

# Readable version for reference:
# {
#     "ASIN":    "asin",
#     "评论人":   "reviewer_name",
#     "评论人标记": "reviewer_id",
#     "是否vp":   "is_verified_purchase",
#     "评论时间":  "review_date",
#     "标题":     "review_title",
#     "内容":     "review_content",
#     "变体属性":  "variant",
#     "星级":     "rating",
#     "赞同数":   "helpful_votes",
#     "站点来源":  "marketplace",
#     "是否图片":  "has_image",
#     "是否有视频": "has_video",
#     "链接":     "review_link",
# }


# ---------------------------------------------------------------------------
# Boolean mapping for 是/否 fields
# ---------------------------------------------------------------------------
_BOOL_MAP = {
    "是": True, "Yes": True, "yes": True, "TRUE": True, "true": True, "1": True,
    "否": False, "No": False, "no": False, "FALSE": False, "false": False, "0": False,
}


# ---------------------------------------------------------------------------
# Core ingest function
# ---------------------------------------------------------------------------
def ingest_reviews(file_obj=None, xlsx_path: str | None = None) -> pd.DataFrame:
    """
    Ingest a Sorftime Excel file and return a cleaned DataFrame.

    Args:
        file_obj:  A file-like object (e.g. from Streamlit file_uploader).
        xlsx_path: Path to an .xlsx file on disk.

    Returns:
        Cleaned pandas DataFrame with English column names.
    """
    # --- Load ---
    if file_obj is not None:
        df = pd.read_excel(file_obj, engine="openpyxl")
    elif xlsx_path is not None:
        df = pd.read_excel(xlsx_path, engine="openpyxl")
    else:
        raise ValueError("Provide either file_obj or xlsx_path")

    print(f"[Review Ingestor] Raw shape: {df.shape[0]} rows x {df.shape[1]} cols")

    # --- Rename columns ---
    df.rename(columns=CHINESE_TO_ENGLISH_MAP, inplace=True)

    # --- Clean: rating (ensure numeric) ---
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")

    # --- Clean: helpful_votes (fill NaN with 0, cast to int) ---
    df["helpful_votes"] = pd.to_numeric(df["helpful_votes"], errors="coerce").fillna(0).astype(int)

    # --- Clean: review_date (parse "December 25, 2025" format) ---
    df["review_date"] = pd.to_datetime(df["review_date"], format="mixed", dayfirst=False)

    # --- Clean: is_verified_purchase (是/否 → True/False) ---
    df["is_verified_purchase"] = df["is_verified_purchase"].map(_BOOL_MAP).fillna(False)

    # --- Clean: has_image, has_video (是/否 → True/False) ---
    df["has_image"] = df["has_image"].map(_BOOL_MAP).fillna(False)
    df["has_video"] = df["has_video"].map(_BOOL_MAP).fillna(False)

    # --- Clean: fill missing text fields with empty string ---
    for col in ("review_title", "review_content", "variant", "reviewer_name"):
        if col in df.columns:
            df[col] = df[col].fillna("")

    # --- Computed: sentiment_bucket ---
    df["sentiment_bucket"] = df["rating"].apply(
        lambda r: "happy" if r >= 4 else "defect" if pd.notna(r) else "unknown"
    )

    # --- Computed: review_length ---
    df["review_length"] = df["review_content"].str.len()

    print(f"[Review Ingestor] Cleaned shape: {df.shape[0]} rows x {df.shape[1]} cols")
    return df


# ---------------------------------------------------------------------------
# Save to Parquet + Debug CSV
# ---------------------------------------------------------------------------
def save_parquet(df: pd.DataFrame) -> str:
    """Save DataFrame to Parquet and debug CSV. Returns parquet path."""
    os.makedirs(_PROCESSED_DIR, exist_ok=True)

    # If existing parquet exists, append and dedup
    if os.path.exists(_PARQUET_FILE):
        existing = pd.read_parquet(_PARQUET_FILE)
        df = pd.concat([existing, df], ignore_index=True)
        df.drop_duplicates(subset=["asin", "reviewer_id"], keep="last", inplace=True)
        print(f"[Review Ingestor] Merged with existing. Total: {len(df)} rows")

    df.to_parquet(_PARQUET_FILE, index=False)
    print(f"[Review Ingestor] Saved Parquet: {_PARQUET_FILE}")

    # Debug CSV (first 50 rows)
    df.head(50).to_csv(_DEBUG_CSV, index=False)
    print(f"[Review Ingestor] Saved debug CSV: {_DEBUG_CSV} (first 50 rows)")

    return _PARQUET_FILE


# ---------------------------------------------------------------------------
# Batch ingest all .xlsx files in raw directory
# ---------------------------------------------------------------------------
def ingest_all() -> pd.DataFrame:
    """Scan data/raw/source_2_review/*.xlsx, ingest all, save to Parquet."""
    pattern = os.path.join(_RAW_DIR, "*.xlsx")
    files = sorted(
        f for f in glob.glob(pattern)
        if not os.path.basename(f).startswith("~$")
    )

    if not files:
        print(f"[Review Ingestor] No .xlsx files found in {_RAW_DIR}")
        return pd.DataFrame()

    frames = []
    for path in files:
        print(f"[Review Ingestor] Reading: {path}")
        df = ingest_reviews(xlsx_path=path)
        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)
    combined.drop_duplicates(subset=["asin", "reviewer_id"], keep="last", inplace=True)
    print(f"[Review Ingestor] Combined: {len(combined)} unique reviews")

    save_parquet(combined)
    print(f"[Review Ingestor] Done. Final shape: {combined.shape[0]} rows x {combined.shape[1]} cols")
    return combined


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    result = ingest_all()
    if not result.empty:
        print("\n--- df.info() ---")
        result.info()
        print(f"\n--- Star distribution ---")
        print(result["rating"].value_counts().sort_index())
        print(f"\n--- Sentiment buckets ---")
        print(result["sentiment_bucket"].value_counts())
