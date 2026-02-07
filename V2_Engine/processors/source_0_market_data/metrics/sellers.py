"""
Seller Analytics — Country distribution, revenue share, seller age.

Ported from:
    - views/catalog_summary_07_seller_analytics.py
    - views/catalog_summary_07a_global_seller_metrics.py
All Streamlit display code removed.

Key legacy functions preserved:
    - parse_date()               → 9-format date parser + regex fallback
    - calculate_months_between() → month delta
    - identify_column()          → now uses ColumnResolver
"""

from __future__ import annotations

import re
from datetime import datetime

import numpy as np
import pandas as pd

from ..core.cleaning import clean_and_average
from ..core.columns import ColumnResolver


# Column candidate lists
SELLER_COUNTRY_CANDIDATES = [
    "Seller Country", "Country", "Merchant Country",
    "Seller Origin", "Seller Country/Region",
]
REVENUE_CANDIDATES = [
    "ASIN Revenue", "Revenue", "Parent Level Revenue",
    "Monthly Revenue", "Estimated Revenue", "Total Revenue",
    "Market Volume",
]
SALES_CANDIDATES = [
    "ASIN Sales", "Sales", "Parent Level Sales",
    "Monthly Sales", "Estimated Sales", "Total Sales",
    "Average Month Sales",
]
CREATION_DATE_CANDIDATES = [
    "Creation Date", "Seller Since", "Store Creation Date",
    "Start Date", "Launch Date", "Seller Launch Date",
]

# Key countries tracked by the legacy system
TRACKED_COUNTRIES = ["AMZ", "US", "CN", "HK", "UK", "DE", "FR", "IT", "ES"]


# ------------------------------------------------------------------
# Date parsing helpers (ported from legacy)
# ------------------------------------------------------------------

def _parse_date(date_str) -> datetime | None:
    """Parse a date string using 9 format patterns plus regex fallback."""
    if pd.isna(date_str):
        return None
    if isinstance(date_str, datetime):
        return date_str

    s = str(date_str)
    formats = [
        "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%b %Y", "%B %Y",
        "%Y/%m/%d", "%d-%b-%Y", "%d-%B-%Y", "%Y%m%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue

    # Regex fallback: YYYY-MM or YYYY/MM
    m = re.search(r"(\d{4})[-/](\d{1,2})", s)
    if m:
        return datetime(int(m.group(1)), int(m.group(2)), 1)

    return None


def _months_between(start: datetime, end: datetime) -> int:
    return (end.year - start.year) * 12 + (end.month - start.month)


# ------------------------------------------------------------------
# Main entry point
# ------------------------------------------------------------------

def calculate_seller_metrics(df: pd.DataFrame) -> dict:
    """
    Compute seller analytics: country distribution, revenue share, seller age.

    Returns:
        {
          "seller_country_column": "Seller Country" | null,
          "revenue_column":       "ASIN Revenue" | null,
          "country_distribution": {
            "AMZ": {"count": 25, "pct": 10.2, "revenue_share": 15.3},
            "US":  {"count": 98, ...},
            "CN":  {"count": 120, ...},
            ...
            "Other": {"count": 15, ...}
          },
          "amazon_dominance_pct": 15.3,
          "avg_seller_age_months": 24.5,
          "total_sellers": 487
        }
    """
    country_col = ColumnResolver.resolve(df, SELLER_COUNTRY_CANDIDATES)
    revenue_col = ColumnResolver.resolve(df, REVENUE_CANDIDATES)
    sales_col = ColumnResolver.resolve(df, SALES_CANDIDATES)
    date_col = ColumnResolver.resolve(df, CREATION_DATE_CANDIDATES)

    # Use revenue if found, otherwise fall back to sales
    value_col = revenue_col or sales_col

    result: dict = {
        "seller_country_column": country_col,
        "revenue_column": value_col,
        "total_sellers": len(df),
    }

    # --- Country distribution ---
    if country_col and country_col in df.columns:
        countries = df[country_col].astype(str)
        total = len(countries)

        # Compute total revenue for share calculation
        total_revenue = 0.0
        if value_col and value_col in df.columns:
            cleaned = pd.to_numeric(
                df[value_col].astype(str).str.replace(r"[\$,]", "", regex=True),
                errors="coerce",
            )
            total_revenue = float(cleaned.sum()) if cleaned.notna().any() else 0.0

        distribution: dict[str, dict] = {}
        seen_countries = set()

        for code in TRACKED_COUNTRIES:
            mask = countries == code
            count = int(mask.sum())
            if count == 0:
                continue
            seen_countries.add(code)

            rev_share = 0.0
            if total_revenue > 0 and value_col and value_col in df.columns:
                country_rev = float(cleaned[mask].sum())
                rev_share = round((country_rev / total_revenue) * 100, 1)

            distribution[code] = {
                "count": count,
                "pct": round((count / total) * 100, 1),
                "revenue_share": rev_share,
            }

        # "Other" bucket
        other_mask = ~countries.isin(TRACKED_COUNTRIES)
        other_count = int(other_mask.sum())
        if other_count > 0:
            other_rev_share = 0.0
            if total_revenue > 0 and value_col and value_col in df.columns:
                other_rev = float(cleaned[other_mask].sum())
                other_rev_share = round((other_rev / total_revenue) * 100, 1)
            distribution["Other"] = {
                "count": other_count,
                "pct": round((other_count / total) * 100, 1),
                "revenue_share": other_rev_share,
            }

        result["country_distribution"] = distribution

        # Amazon dominance
        amz = distribution.get("AMZ", {})
        result["amazon_dominance_pct"] = amz.get("revenue_share", 0.0)
    else:
        result["country_distribution"] = {}
        result["amazon_dominance_pct"] = None

    # --- Average seller age ---
    if date_col and date_col in df.columns:
        now = datetime.now()
        ages: list[int] = []
        for raw in df[date_col].dropna():
            dt = _parse_date(raw)
            if dt:
                ages.append(_months_between(dt, now))
        result["avg_seller_age_months"] = round(float(np.mean(ages)), 1) if ages else None
    else:
        result["avg_seller_age_months"] = None

    return result
