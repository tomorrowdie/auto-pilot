"""
Column Resolver — Flexible column-name detection for H10 Xray data.

Ported from:
    - views/catalog_summary.py :: find_column_in_dataframe()      (3-tier matching)
    - views/catalog_summary.py :: prepare_dataframe_for_pricing()  (price/fee detection)
    - views/amazon_data_process_h10.py :: select_important_columns()

H10 Xray exports change column names across versions.
This module centralises all column-name resolution into one place.
"""

from __future__ import annotations

import pandas as pd


class ColumnResolver:
    """
    Finds columns in a DataFrame regardless of exact spelling or casing.

    Resolution order (first match wins):
        1. Exact name match
        2. Partial match  — candidate is a substring of a real column (case-insensitive)
        3. Keyword match  — any word from candidate appears in a real column
    """

    # ----- pre-built candidate lists for common H10 fields -----

    PRICE_CANDIDATES = [
        "Price US$", "Price US", "Average Price US$",
        "Price USD", "Price", "PriceUS",
    ]

    FEE_CANDIDATES = [
        "Fees US$", "Fees US", "Average Fees US$",
        "Fees USD", "Fees", "FeesUS",
    ]

    BSR_CANDIDATES = [
        "BSR", "Best Sellers Rank", "BestSellersRank", "Best Seller Rank",
    ]

    RATING_CANDIDATES = [
        "Rating", "Product Rating", "Star Rating", "Stars", "Average Rating",
    ]

    REVIEW_COUNT_CANDIDATES = [
        "Review Count", "Reviews", "Number of Reviews",
        "ReviewCount", "Total Reviews",
    ]

    REVIEW_VELOCITY_CANDIDATES = [
        "Review Velocity", "ReviewVelocity",
        "Reviews Per Month", "Monthly Reviews",
    ]

    IMAGES_CANDIDATES = [
        "Images", "Image Count", "Number of Images",
        "ImageCount", "Product Images",
    ]

    PRIORITY_DISPLAY = [
        "Display Order", "Product Details", "ASIN", "Brand", "Price US",
        "BSR", "Organic VS Ads", "Sales Rank (ALL)",
        "Organic Rank", "Ad Rank", "Source Files",
    ]

    # ----------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------

    @staticmethod
    def resolve(df: pd.DataFrame, candidates: list[str]) -> str | None:
        """
        Find the best-matching column in *df* from a list of candidates.

        Returns:
            The matched column name, or None if nothing matches.
        """
        columns = list(df.columns)

        # Tier 1: exact match
        for name in candidates:
            if name in columns:
                return name

        # Tier 2: partial match (case-insensitive)
        col_lower = {c: c.lower() for c in columns}
        for name in candidates:
            name_low = name.lower()
            for col, col_low in col_lower.items():
                if name_low in col_low:
                    return col

        # Tier 3: keyword match
        keywords = []
        for name in candidates:
            keywords.extend(name.lower().split())
        for col, col_low in col_lower.items():
            for kw in keywords:
                if kw in col_low:
                    return col

        return None

    @classmethod
    def resolve_pricing(cls, df: pd.DataFrame) -> tuple[str, str]:
        """
        Find the Price and Fee columns in *df*.

        Returns:
            (price_column, fee_column) — uses placeholder names if not found.
        """
        price_col = cls.resolve(df, cls.PRICE_CANDIDATES)
        fee_col = cls.resolve(df, cls.FEE_CANDIDATES)

        if price_col is None:
            price_col = "Price_Placeholder"
        if fee_col is None:
            fee_col = "Fee_Placeholder"

        return price_col, fee_col

    @classmethod
    def priority_columns(cls, df: pd.DataFrame) -> list[str]:
        """Return the subset of PRIORITY_DISPLAY columns that exist in *df*."""
        return [c for c in cls.PRIORITY_DISPLAY if c in df.columns]
