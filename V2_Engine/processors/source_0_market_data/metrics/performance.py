"""
Product Performance Metrics — BSR, Ratings, Reviews, Images.

Ported from: views/catalog_summary_05_product_performance.py
All Streamlit display code removed.

Uses core.columns.ColumnResolver   (replaces ad-hoc candidate searching)
Uses core.cleaning.clean_and_average (replaces 5th duplicated copy)
Uses core.ranking.get_rank_range   (replaces 6th duplicated copy)
"""

from __future__ import annotations

import pandas as pd

from ..core.cleaning import clean_and_average
from ..core.columns import ColumnResolver
from ..core.ranking import RANK_CATEGORIES, get_rank_range


# Metric definitions: (output key, candidate list, format hint)
_METRICS = [
    ("avg_bsr",             ColumnResolver.BSR_CANDIDATES),
    ("avg_rating",          ColumnResolver.RATING_CANDIDATES),
    ("avg_review_count",    ColumnResolver.REVIEW_COUNT_CANDIDATES),
    ("review_velocity",     ColumnResolver.REVIEW_VELOCITY_CANDIDATES),
    ("avg_images",          ColumnResolver.IMAGES_CANDIDATES),
]


def calculate_performance_metrics(
    df: pd.DataFrame,
    rank_column: str = "Sales Rank (ALL)",
) -> dict:
    """
    Compute product performance averages for every rank tier.

    Args:
        df:          Cleaned DataFrame (output of H10Ingestor).
        rank_column: Which rank column to bucket by.

    Returns:
        {
          "rank_column": "Sales Rank (ALL)",
          "resolved_columns": {
            "avg_bsr": "BSR",
            "avg_rating": null,        # null = not found in data
            ...
          },
          "by_rank": {
            "#1-10": {
              "count": 10,
              "avg_bsr": 12345.0,
              "avg_rating": 4.3,
              ...
            },
            ...
          },
          "totals": {
            "total_products": 982,
            "avg_bsr": 54321.0,
            ...
          }
        }
    """
    if rank_column not in df.columns:
        return {"error": f"Rank column '{rank_column}' not found in DataFrame"}

    # Resolve which actual columns exist for each metric
    resolved: dict[str, str | None] = {}
    for key, candidates in _METRICS:
        resolved[key] = ColumnResolver.resolve(df, candidates)

    # If nothing at all was found, report it
    if all(v is None for v in resolved.values()):
        return {
            "rank_column": rank_column,
            "resolved_columns": resolved,
            "note": "No performance columns found in this dataset",
            "by_rank": {},
            "totals": {"total_products": len(df)},
        }

    by_rank: dict[str, dict] = {}

    for cat in RANK_CATEGORIES:
        min_r, max_r = get_rank_range(cat)
        bucket = df[(df[rank_column] >= min_r) & (df[rank_column] <= max_r)]
        entry: dict = {"count": len(bucket)}

        for key, _ in _METRICS:
            col = resolved[key]
            if col is not None and len(bucket) > 0:
                val = clean_and_average(bucket, col)
                entry[key] = round(val, 2) if val is not None else None
            else:
                entry[key] = None

        by_rank[cat] = entry

    # Market-wide totals
    totals: dict = {"total_products": len(df)}
    for key, _ in _METRICS:
        col = resolved[key]
        if col is not None:
            val = clean_and_average(df, col)
            totals[key] = round(val, 2) if val is not None else None
        else:
            totals[key] = None

    return {
        "rank_column": rank_column,
        "resolved_columns": resolved,
        "by_rank": by_rank,
        "totals": totals,
    }
