"""
Pricing & Profitability Metrics — Pure calculation engine.

Ported from: views/catalog_summary_04_pricing.py
All Streamlit display code removed.

Uses core.columns.ColumnResolver  (replaces ad-hoc column detection)
Uses core.ranking.get_rank_range  (replaces 5 duplicated copies)
"""

from __future__ import annotations

import pandas as pd

from ..core.columns import ColumnResolver
from ..core.ranking import RANK_CATEGORIES, get_rank_range


def _clean_series(series: pd.Series) -> pd.Series:
    """Strip $/, convert to numeric, return Series (NaNs preserved)."""
    return pd.to_numeric(
        series.astype(str).str.replace(r"[\$,]", "", regex=True),
        errors="coerce",
    )


def calculate_pricing_metrics(
    df: pd.DataFrame,
    rank_column: str = "Sales Rank (ALL)",
) -> dict:
    """
    Compute pricing statistics for every rank tier.

    Args:
        df:          Cleaned DataFrame (output of H10Ingestor).
        rank_column: Which rank column to bucket by.

    Returns:
        {
          "rank_column": "Sales Rank (ALL)",
          "price_column": "Price US",
          "fee_column":   "Fee_Placeholder",
          "by_rank": {
            "#1-10": {
              "count": 10,
              "avg_price": 24.99,
              "avg_fee":    5.12,
              "avg_profit": 19.87,
              "std_dev":    4.33,
              "p25": 19.99, "p50": 24.99, "p75": 29.99,
              "max": 49.99
            },
            ...
          },
          "totals": {
            "total_products": 982,
            "avg_price": 22.50,
            "avg_fee":    4.80,
            "avg_profit": 17.70,
            "median_price": 21.99,
            "min_price": 5.99,
            "max_price": 89.99
          }
        }
    """
    if rank_column not in df.columns:
        return {"error": f"Rank column '{rank_column}' not found in DataFrame"}

    price_col, fee_col = ColumnResolver.resolve_pricing(df)

    # Check if we need placeholder data
    has_price = price_col in df.columns
    has_fee = fee_col in df.columns

    if not has_price:
        return {"error": f"No price column found (tried {ColumnResolver.PRICE_CANDIDATES})"}

    # Pre-clean the full columns once (avoids repeated regex per bucket)
    prices_all = _clean_series(df[price_col]) if has_price else pd.Series(dtype=float)
    fees_all = _clean_series(df[fee_col]) if has_fee else pd.Series(0.0, index=df.index)

    by_rank: dict[str, dict] = {}

    for cat in RANK_CATEGORIES:
        min_r, max_r = get_rank_range(cat)
        mask = (df[rank_column] >= min_r) & (df[rank_column] <= max_r)
        bucket_prices = prices_all[mask].dropna()
        bucket_fees = fees_all[mask].dropna()
        count = int(mask.sum())

        if count == 0 or len(bucket_prices) == 0:
            by_rank[cat] = {"count": count}
            continue

        avg_price = float(bucket_prices.mean())
        avg_fee = float(bucket_fees.mean()) if len(bucket_fees) > 0 else 0.0

        by_rank[cat] = {
            "count":      count,
            "avg_price":  round(avg_price, 2),
            "avg_fee":    round(avg_fee, 2),
            "avg_profit": round(avg_price - avg_fee, 2),
            "std_dev":    round(float(bucket_prices.std()), 2) if len(bucket_prices) > 1 else 0.0,
            "p25":        round(float(bucket_prices.quantile(0.25)), 2),
            "p50":        round(float(bucket_prices.quantile(0.50)), 2),
            "p75":        round(float(bucket_prices.quantile(0.75)), 2),
            "max":        round(float(bucket_prices.max()), 2),
        }

    # Market-wide totals
    valid_prices = prices_all.dropna()
    valid_fees = fees_all.dropna()
    avg_p = float(valid_prices.mean()) if len(valid_prices) > 0 else 0.0
    avg_f = float(valid_fees.mean()) if len(valid_fees) > 0 else 0.0

    totals = {
        "total_products": len(df),
        "avg_price":      round(avg_p, 2),
        "avg_fee":        round(avg_f, 2),
        "avg_profit":     round(avg_p - avg_f, 2),
        "median_price":   round(float(valid_prices.median()), 2) if len(valid_prices) > 0 else 0.0,
        "min_price":      round(float(valid_prices.min()), 2) if len(valid_prices) > 0 else 0.0,
        "max_price":      round(float(valid_prices.max()), 2) if len(valid_prices) > 0 else 0.0,
    }

    return {
        "rank_column":  rank_column,
        "price_column": price_col,
        "fee_column":   fee_col,
        "by_rank":      by_rank,
        "totals":       totals,
    }
