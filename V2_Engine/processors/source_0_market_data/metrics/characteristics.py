"""
Product Characteristics Metrics — Weight, Dimensions, Size Tier, Category.

Ported from: views/catalog_summary_06_product_characteristics.py
All Streamlit display code removed.

Key legacy functions preserved:
    - extract_numeric_values()  → weight parsing with oz/kg → lbs conversion
    - calculate_average_dimensions() → regex L x W x H → volume (in³)
    - calculate_size_distribution()  → value_counts → top 2 with %
    - calculate_category_distribution() → value_counts → top category
    - calculate_aba_click_positions()   → Counter-based position analysis
"""

from __future__ import annotations

import re
from collections import Counter

import numpy as np
import pandas as pd

from ..core.columns import ColumnResolver
from ..core.ranking import RANK_CATEGORIES, get_rank_range


# Column candidate lists
WEIGHT_CANDIDATES = [
    "Weight", "Item Weight", "Product Weight", "Net Weight", "Ship Weight",
]
DIMENSION_CANDIDATES = [
    "Dimensions", "Product Dimensions", "Item Dimensions",
    "Package Dimensions", "Size",
]
SIZE_TIER_CANDIDATES = [
    "Size", "Size Tier", "Product Size", "Package Size",
]
CATEGORY_CANDIDATES = [
    "Category", "Department", "Product Category", "Product Type", "Type",
]
ABA_CLICK_CANDIDATES = [
    "ABA Most Clicked", "ABA Click Position", "Most Clicked Position",
]


# ------------------------------------------------------------------
# Pure helper functions (ported from legacy, zero UI)
# ------------------------------------------------------------------

def _extract_weights(series: pd.Series) -> pd.Series:
    """
    Extract numeric weight values from a string Series.
    Converts oz → lbs (÷16), kg → lbs (×2.20462).
    Falls back to plain numeric extraction if no unit found.
    """
    values: list[float] = []
    for raw in series.dropna():
        s = str(raw).lower()
        matches = re.findall(
            r"(\d+\.?\d*)\s*(?:lbs?|pounds?|oz|ounces?|kg|kilograms?)", s
        )
        if matches:
            w = float(matches[0])
            if "oz" in s or "ounce" in s:
                w /= 16
            elif "kg" in s or "kilogram" in s:
                w *= 2.20462
            values.append(w)
        else:
            plain = re.findall(r"^(\d+\.?\d*)$", s.strip())
            if plain:
                values.append(float(plain[0]))
    return pd.Series(values, dtype=float)


def _extract_volume(series: pd.Series) -> list[float]:
    """
    Parse "L x W x H" dimension strings and return volumes (in³).
    Handles formats like '10 x 5 x 2 inches', '10" x 5" x 2"'.
    """
    pattern = re.compile(
        r"(\d+\.?\d*)\s*[\"']?\s*x\s*(\d+\.?\d*)\s*[\"']?\s*x\s*(\d+\.?\d*)"
    )
    volumes: list[float] = []
    for raw in series.dropna():
        m = pattern.search(str(raw).lower())
        if m:
            l, w, h = float(m.group(1)), float(m.group(2)), float(m.group(3))
            volumes.append(l * w * h)
    return volumes


def _top_n_distribution(series: pd.Series, n: int = 2) -> list[dict]:
    """
    Return the top-N values from a Series with counts and percentages.
    Example: [{"value": "Standard", "count": 45, "pct": 72.6}, ...]
    """
    counts = series.value_counts()
    total = len(series)
    if total == 0 or counts.empty:
        return []
    result = []
    for val, cnt in counts.head(n).items():
        result.append({
            "value": str(val),
            "count": int(cnt),
            "pct": round((cnt / total) * 100, 1),
        })
    return result


def _top_aba_position(series: pd.Series) -> int | None:
    """
    Find the most frequent ABA click position.
    If tied, return the lowest position number.
    """
    positions: list[int] = []
    for raw in series.dropna():
        matches = re.findall(r"(?:position\s*)?(\d+)", str(raw).lower())
        if matches:
            positions.append(int(matches[0]))
    if not positions:
        return None
    counts = Counter(positions)
    top_count = counts.most_common(1)[0][1]
    tied = [p for p, c in counts.items() if c == top_count]
    return min(tied)


# ------------------------------------------------------------------
# Main entry point
# ------------------------------------------------------------------

def calculate_characteristics_metrics(
    df: pd.DataFrame,
    rank_column: str = "Sales Rank (ALL)",
) -> dict:
    """
    Compute product characteristics for every rank tier.

    Args:
        df:          Cleaned DataFrame (output of H10Ingestor).
        rank_column: Which rank column to bucket by.

    Returns:
        {
          "rank_column": "Sales Rank (ALL)",
          "resolved_columns": {
            "weight": "Item Weight" | null,
            "dimensions": null,
            ...
          },
          "by_rank": {
            "#1-10": {
              "count": 10,
              "avg_weight_lbs": 1.52,
              "avg_volume_in3": 120.5,
              "size_distribution": [{"value": "Standard", "count": 8, "pct": 80.0}],
              "top_category": {"value": "Baby", "count": 6, "pct": 60.0},
              "top_aba_position": 1
            },
            ...
          },
          "totals": { ... }
        }
    """
    if rank_column not in df.columns:
        return {"error": f"Rank column '{rank_column}' not found in DataFrame"}

    # Resolve columns
    weight_col = ColumnResolver.resolve(df, WEIGHT_CANDIDATES)
    dim_col = ColumnResolver.resolve(df, DIMENSION_CANDIDATES)
    size_col = ColumnResolver.resolve(df, SIZE_TIER_CANDIDATES)
    cat_col = ColumnResolver.resolve(df, CATEGORY_CANDIDATES)
    aba_col = ColumnResolver.resolve(df, ABA_CLICK_CANDIDATES)

    resolved = {
        "weight": weight_col,
        "dimensions": dim_col,
        "size_tier": size_col,
        "category": cat_col,
        "aba_click": aba_col,
    }

    if all(v is None for v in resolved.values()):
        return {
            "rank_column": rank_column,
            "resolved_columns": resolved,
            "note": "No characteristics columns found in this dataset",
            "by_rank": {},
            "totals": {"total_products": len(df)},
        }

    def _compute_bucket(subset: pd.DataFrame) -> dict:
        entry: dict = {"count": len(subset)}
        if len(subset) == 0:
            return entry

        # Weight
        if weight_col and weight_col in subset.columns:
            weights = _extract_weights(subset[weight_col])
            entry["avg_weight_lbs"] = round(float(weights.mean()), 2) if len(weights) > 0 else None
        else:
            entry["avg_weight_lbs"] = None

        # Dimensions → volume
        if dim_col and dim_col in subset.columns:
            volumes = _extract_volume(subset[dim_col])
            entry["avg_volume_in3"] = round(float(np.mean(volumes)), 1) if volumes else None
        else:
            entry["avg_volume_in3"] = None

        # Size tier distribution
        if size_col and size_col in subset.columns:
            entry["size_distribution"] = _top_n_distribution(subset[size_col], n=2)
        else:
            entry["size_distribution"] = []

        # Category distribution
        if cat_col and cat_col in subset.columns:
            top = _top_n_distribution(subset[cat_col], n=1)
            entry["top_category"] = top[0] if top else None
        else:
            entry["top_category"] = None

        # ABA click position
        if aba_col and aba_col in subset.columns:
            entry["top_aba_position"] = _top_aba_position(subset[aba_col])
        else:
            entry["top_aba_position"] = None

        return entry

    by_rank: dict[str, dict] = {}
    for cat in RANK_CATEGORIES:
        min_r, max_r = get_rank_range(cat)
        bucket = df[(df[rank_column] >= min_r) & (df[rank_column] <= max_r)]
        by_rank[cat] = _compute_bucket(bucket)

    totals = _compute_bucket(df)
    totals["total_products"] = len(df)

    return {
        "rank_column": rank_column,
        "resolved_columns": resolved,
        "by_rank": by_rank,
        "totals": totals,
    }
