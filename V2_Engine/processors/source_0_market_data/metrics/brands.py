"""
Brand Analytics — Top brands, market share, HHI concentration index.

Ported from: views/catalog_summary_08_detailed_analysis.py
             (display_competitive_analysis function)
All Streamlit display code removed.

NEW AI METRIC: Herfindahl-Hirschman Index (HHI)
    HHI = sum( (brand_share_%)^2 )
    < 1500  → Competitive (fragmented market, easy entry)
    1500-2500 → Moderately Concentrated
    > 2500  → Highly Concentrated (dominated by few brands)
"""

from __future__ import annotations

import pandas as pd

from ..core.cleaning import clean_and_average
from ..core.columns import ColumnResolver


# Column candidates for brand
BRAND_CANDIDATES = ["Brand", "Brand Name", "Manufacturer", "Seller"]


def calculate_brand_metrics(
    df: pd.DataFrame,
    top_n: int = 10,
) -> dict:
    """
    Compute brand-level analytics and market concentration (HHI).

    Args:
        df:    Cleaned DataFrame (output of H10Ingestor).
        top_n: Number of top brands to include in the breakdown.

    Returns:
        {
          "brand_column": "Brand",
          "total_products": 487,
          "total_brands": 85,
          "top_brands": [
            {
              "brand": "BrandX",
              "product_count": 12,
              "market_share_pct": 8.5,
              "avg_price": 24.99,
              "avg_rating": 4.3,
              "avg_bsr": 12000,
              "avg_sales": 150
            },
            ...
          ],
          "hhi": {
            "score": 842,
            "classification": "Competitive",
            "interpretation": "Fragmented market — no single brand dominates."
          }
        }
    """
    brand_col = ColumnResolver.resolve(df, BRAND_CANDIDATES)
    if not brand_col or brand_col not in df.columns:
        return {"error": "No brand column found in DataFrame"}

    # Resolve optional metric columns
    price_col, _ = ColumnResolver.resolve_pricing(df)
    has_price = price_col in df.columns

    revenue_col = ColumnResolver.resolve(df, [
        "ASIN Revenue", "Revenue", "Parent Level Revenue",
        "Monthly Revenue", "Total Revenue",
    ])
    sales_col = ColumnResolver.resolve(df, [
        "ASIN Sales", "Sales", "Parent Level Sales",
        "Monthly Sales", "Total Sales", "Keyword Sales",
    ])
    bsr_col = ColumnResolver.resolve(df, ColumnResolver.BSR_CANDIDATES)
    rating_col = ColumnResolver.resolve(df, ColumnResolver.RATING_CANDIDATES)

    # Use revenue for market share; fall back to sales
    share_col = revenue_col or sales_col

    # --- Brand aggregation ---
    brands = df[brand_col].astype(str)
    brand_counts = brands.value_counts()
    total_products = len(df)
    total_brands = len(brand_counts)

    # Pre-clean share column once
    share_values: pd.Series | None = None
    total_share_value = 0.0
    if share_col and share_col in df.columns:
        share_values = pd.to_numeric(
            df[share_col].astype(str).str.replace(r"[\$,]", "", regex=True),
            errors="coerce",
        )
        total_share_value = float(share_values.sum()) if share_values.notna().any() else 0.0

    # Build top-N brand list
    top_brand_names = brand_counts.head(top_n).index.tolist()
    top_brands: list[dict] = []

    for brand_name in top_brand_names:
        mask = brands == brand_name
        subset = df[mask]
        count = int(mask.sum())

        entry: dict = {
            "brand": brand_name,
            "product_count": count,
        }

        # Market share
        if share_values is not None and total_share_value > 0:
            brand_value = float(share_values[mask].sum())
            entry["market_share_pct"] = round((brand_value / total_share_value) * 100, 2)
        else:
            # Fall back to product-count share
            entry["market_share_pct"] = round((count / total_products) * 100, 2)

        # Optional averages
        if has_price:
            entry["avg_price"] = _safe_avg(subset, price_col)
        if rating_col and rating_col in subset.columns:
            entry["avg_rating"] = _safe_avg(subset, rating_col)
        if bsr_col and bsr_col in subset.columns:
            entry["avg_bsr"] = _safe_avg(subset, bsr_col)
        if sales_col and sales_col in subset.columns:
            entry["avg_sales"] = _safe_avg(subset, sales_col)

        top_brands.append(entry)

    # --- HHI calculation (ALL brands, not just top N) ---
    hhi_score = _calculate_hhi(brands, share_values, total_share_value, total_products)

    if hhi_score < 1500:
        classification = "Competitive"
        interpretation = "Fragmented market — no single brand dominates. Easier entry."
    elif hhi_score < 2500:
        classification = "Moderately Concentrated"
        interpretation = "A few brands hold significant share. Entry requires differentiation."
    else:
        classification = "Highly Concentrated"
        interpretation = "Market dominated by few brands. Entry is difficult and expensive."

    return {
        "brand_column": brand_col,
        "total_products": total_products,
        "total_brands": total_brands,
        "top_brands": top_brands,
        "hhi": {
            "score": round(hhi_score, 1),
            "classification": classification,
            "interpretation": interpretation,
        },
    }


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _safe_avg(subset: pd.DataFrame, col: str) -> float | None:
    """Clean a column and return its mean, or None."""
    val = clean_and_average(subset, col)
    return round(val, 2) if val is not None else None


def _calculate_hhi(
    brands: pd.Series,
    share_values: pd.Series | None,
    total_share_value: float,
    total_products: int,
) -> float:
    """
    Herfindahl-Hirschman Index across ALL brands.

    HHI = sum( share_i^2 )  where share_i is in percentage points (0-100).
    """
    if share_values is not None and total_share_value > 0:
        # Revenue-based HHI
        brand_revenues = share_values.groupby(brands).sum()
        shares = (brand_revenues / total_share_value) * 100
    else:
        # Product-count-based HHI (fallback)
        brand_counts = brands.value_counts()
        shares = (brand_counts / total_products) * 100

    return float((shares ** 2).sum())
