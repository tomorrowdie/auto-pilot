"""
Ranking — Organic/Ads classification and rank-bucket utilities.

Ported from:
    - views/amazon_data_process_h10.py  :: update_rank_columns()
    - views/catalog_summary.py          :: categorize_by_rank(), get_rank_range()

All Streamlit code removed. Pure Pandas/NumPy logic.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


# Standard rank buckets used throughout the system
RANK_CATEGORIES = [
    "#1-10", "#11-30", "31-50", "51-100",
    "101-150", "151-200", "201-300", "301+",
]


def calculate_ranks(df: pd.DataFrame) -> pd.DataFrame:
    """
    Classify rows as Organic/Ads and assign ranking columns.

    Adds three columns:
        - 'Sales Rank (ALL)'  — sequential 1..N
        - 'Organic VS Ads'    — 'Organic' or 'Ads' (based on '($)' in Product Details)
        - 'Organic Rank'      — sequential rank within Organic rows
        - 'Ad Rank'           — sequential rank within Ads rows

    Args:
        df: DataFrame with at least a 'Product Details' column.

    Returns:
        A new DataFrame with the ranking columns added.
    """
    out = df.copy()

    # Sales Rank (ALL): simple 1..N
    out["Sales Rank (ALL)"] = range(1, len(out) + 1)

    # Organic vs Ads classification — legacy rule: '($)' in Product Details = Ads
    if "Product Details" in out.columns:
        out["Organic VS Ads"] = out["Product Details"].apply(
            lambda x: "Ads" if "($)" in str(x) else "Organic"
        )
    else:
        out["Organic VS Ads"] = "Organic"

    # Separate rank columns
    out["Organic Rank"] = pd.NA
    out["Ad Rank"] = pd.NA

    organic_mask = out["Organic VS Ads"] == "Organic"
    ads_mask = out["Organic VS Ads"] == "Ads"

    out.loc[organic_mask, "Organic Rank"] = range(1, organic_mask.sum() + 1)
    out.loc[ads_mask, "Ad Rank"] = range(1, ads_mask.sum() + 1)

    return out


def categorize_by_rank(df: pd.DataFrame, rank_column: str = "Sales Rank (ALL)") -> pd.DataFrame:
    """
    Add a 'Rank Category' column using np.select rank buckets.

    Buckets: #1-10, #11-30, 31-50, 51-100, 101-150, 151-200, 201-300, 301+
    """
    if rank_column not in df.columns:
        return df.copy()

    out = df.copy()

    conditions = [
        out[rank_column] <= 10,
        (out[rank_column] > 10) & (out[rank_column] <= 30),
        (out[rank_column] > 30) & (out[rank_column] <= 50),
        (out[rank_column] > 50) & (out[rank_column] <= 100),
        (out[rank_column] > 100) & (out[rank_column] <= 150),
        (out[rank_column] > 150) & (out[rank_column] <= 200),
        (out[rank_column] > 200) & (out[rank_column] <= 300),
        out[rank_column] > 300,
    ]

    out["Rank Category"] = np.select(conditions, RANK_CATEGORIES, default="Other")
    return out


def get_rank_range(rank_category: str) -> tuple[int, float]:
    """
    Convert a rank category label to (min_rank, max_rank).

    Example:
        get_rank_range('#1-10')  → (1, 10)
        get_rank_range('301+')   → (301, inf)
    """
    _MAP = {
        "#1-10":   (1, 10),
        "#11-30":  (11, 30),
        "31-50":   (31, 50),
        "51-100":  (51, 100),
        "101-150": (101, 150),
        "151-200": (151, 200),
        "201-300": (201, 300),
        "301+":    (301, float("inf")),
    }
    return _MAP.get(rank_category, (0, float("inf")))
