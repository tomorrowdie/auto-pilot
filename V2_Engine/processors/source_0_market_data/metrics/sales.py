"""
Sales & Revenue Metrics — Pure calculation engine.

Ported from: views/catalog_summary_03_sales_revenue.py
All Streamlit display code removed.

Uses core.cleaning.clean_and_average (replaces 4 duplicated copies)
Uses core.ranking.get_rank_range    (replaces 5 duplicated copies)
"""

from __future__ import annotations

import pandas as pd

from ..core.cleaning import clean_and_average
from ..core.ranking import RANK_CATEGORIES, get_rank_range


# Columns the legacy system searched for as sales / revenue metrics
SALES_METRIC_CANDIDATES = [
    "ASIN Sales", "Parent Level Sales", "Recent Purchases",
    "ASIN Revenue", "Parent Level Revenue",
    "Average Monthly Sales", "Sector Sales Estimate",
    "Market Volume",
]

# Fallback keywords if none of the above exist
_FALLBACK_KEYWORDS = ["Sales", "Revenue", "Purchases", "Volume"]


def _detect_sales_columns(df: pd.DataFrame) -> list[str]:
    """Return whichever sales/revenue columns actually exist in *df*."""
    found = [col for col in SALES_METRIC_CANDIDATES if col in df.columns]
    if found:
        return found

    # Fallback: any column whose name contains a relevant keyword
    return [
        col for col in df.columns
        if any(kw.lower() in col.lower() for kw in _FALLBACK_KEYWORDS)
    ]


def calculate_sales_metrics(
    df: pd.DataFrame,
    rank_column: str = "Sales Rank (ALL)",
) -> dict:
    """
    Compute sales & revenue averages for every rank tier.

    Args:
        df:          Cleaned DataFrame (output of H10Ingestor).
        rank_column: Which rank column to bucket by.

    Returns:
        {
          "rank_column": "Sales Rank (ALL)",
          "metrics_columns": ["ASIN Sales", "ASIN Revenue", ...],
          "by_rank": {
            "#1-10":  {"count": 10, "ASIN Sales": 234.5, ...},
            "#11-30": {"count": 20, "ASIN Sales": 189.2, ...},
            ...
          },
          "totals": {
            "total_products": 982,
            "ASIN Sales": 145.3,   # market-wide average
            ...
          }
        }
    """
    if rank_column not in df.columns:
        return {"error": f"Rank column '{rank_column}' not found in DataFrame"}

    metric_cols = _detect_sales_columns(df)
    if not metric_cols:
        return {"error": "No sales/revenue columns detected"}

    by_rank: dict[str, dict] = {}

    for cat in RANK_CATEGORIES:
        min_r, max_r = get_rank_range(cat)
        bucket = df[(df[rank_column] >= min_r) & (df[rank_column] <= max_r)]
        entry: dict = {"count": len(bucket)}

        for col in metric_cols:
            entry[col] = clean_and_average(bucket, col) if len(bucket) > 0 else None

        by_rank[cat] = entry

    # Market-wide totals
    totals: dict = {"total_products": len(df)}
    for col in metric_cols:
        totals[col] = clean_and_average(df, col)

    return {
        "rank_column": rank_column,
        "metrics_columns": metric_cols,
        "by_rank": by_rank,
        "totals": totals,
    }
