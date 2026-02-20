"""
Cleaning — Deduplicated numeric cleaning utilities for Source 0.

Ported from (4 duplicated copies):
    - views/amazon_catalog_insight_h10.py  :: preprocess_df()
    - views/catalog_summary.py             :: clean_and_compute_average()
    - views/catalog_summary_02_summary.py  :: clean_and_compute_average()
    - views/catalog_summary_03_sales_revenue.py :: clean_and_compute_average()

All Streamlit code removed. Pure Pandas logic.
"""

import pandas as pd


# Default columns that H10 Xray exports as strings with commas / dollar signs
DEFAULT_NUMERIC_COLUMNS = [
    "Price US", "BSR", "Review Count", "ASIN Sales",
    "Parent Level Sales", "Recent Purchases", "Parent Level Revenue",
    "ASIN Revenue", "Average Month Sales",
]


def clean_currency(df: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
    """
    Strip '$' and ',' from specified columns, convert to numeric, coerce errors to NaN.

    Args:
        df:      Input DataFrame (not mutated).
        columns: Column names to clean. Defaults to DEFAULT_NUMERIC_COLUMNS.

    Returns:
        A new DataFrame with cleaned numeric columns.
    """
    out = df.copy()
    targets = columns if columns is not None else DEFAULT_NUMERIC_COLUMNS

    for col in targets:
        if col in out.columns:
            out[col] = pd.to_numeric(
                out[col].astype(str).str.replace(r"[\$,]", "", regex=True),
                errors="coerce",
            )
    return out


def clean_and_average(df: pd.DataFrame, column: str) -> float | None:
    """
    Clean a single column and return its mean.

    Strips '$' and ',', coerces to numeric, drops NaN, returns mean.
    Returns 0 if all values are NaN, None if column doesn't exist.
    """
    if column not in df.columns:
        return None

    numeric = pd.to_numeric(
        df[column].astype(str).str.replace(r"[\$,]", "", regex=True),
        errors="coerce",
    ).dropna()

    return numeric.mean() if len(numeric) > 0 else 0


def format_metric(value: float | None, metric_name: str) -> str:
    """
    Format a metric value for display based on the metric type.

    Rules:
        Price / Revenue / Fees → $X.XX
        Sales / Purchases / Volume → integer (or 1 decimal if < 10)
        Everything else → X.XX
    """
    if value is None:
        return ""

    name_lower = metric_name.lower()

    if any(kw in name_lower for kw in ("price", "revenue", "fees", "fee")):
        return f"${value:.2f}"

    if any(kw in name_lower for kw in ("sales", "purchases", "volume")):
        return f"{value:.0f}" if value >= 10 else f"{value:.1f}"

    return f"{value:.2f}"
