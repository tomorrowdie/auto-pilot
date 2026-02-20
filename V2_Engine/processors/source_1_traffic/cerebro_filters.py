"""
Cerebro Filters — Strategy presets and filter engine for keyword data.

Pure data logic. Zero UI knowledge.
Takes a cleaned DataFrame + filter dict, returns a filtered DataFrame.

Usage:
    python -m V2_Engine.processors.source_1_traffic.cerebro_filters
"""

import os

import pandas as pd


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )
    )
)
_PROCESSED_DIR = os.path.join(_BASE_DIR, "data", "processed")


# ---------------------------------------------------------------------------
# Strategy Presets
# ---------------------------------------------------------------------------
_PRESETS = {
    "Level 1": {"search_volume_max": 8000},
    "Level 2": {"search_volume_min": 8000, "search_volume_max": 10000},
    "Level 3": {"search_volume_min": 10000, "search_volume_max": 20000},
    "Level 4": {"search_volume_min": 20000},
    "Tactical": {"search_volume_max": 8000},
    "Custom": {},
}


def get_strategy_preset(name: str) -> dict:
    """
    Return a filter dict for a named strategy.

    Available presets:
        Level 1 / Tactical : search_volume max 8000
        Level 2            : search_volume 8000-10000
        Level 3            : search_volume 10000-20000
        Level 4            : search_volume 20000+
        Custom             : empty dict (no limits)

    Unknown names return an empty dict (same as Custom).
    """
    return dict(_PRESETS.get(name, {}))


# ---------------------------------------------------------------------------
# Filter-key -> column-name mapping
# ---------------------------------------------------------------------------
_MINMAX_MAP = {
    "search_volume":        "search_volume",
    "word_count":           "word_count",
    "competing_products":   "competing_products",
    "sales":                "keyword_sales",
    "title_density":        "title_density",
    "cerebro_iq_score":     "cerebro_iq_score",
    "search_volume_trend":  "search_volume_trend",
    "aba_click_share":      "aba_total_click_share",
    "aba_conv_share":       "aba_total_conv_share",
}

# Match-type label -> column name
_MATCH_TYPE_MAP = {
    "Organic":        "organic",
    "Sponsored":      "sponsored_asins",
    "Smart Complete": "smart_complete",
}


# ---------------------------------------------------------------------------
# Filter Engine
# ---------------------------------------------------------------------------

def apply_cerebro_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """
    Apply all filters to a Cerebro DataFrame (AND logic across filters).

    Supported filter keys:
        {prefix}_min / {prefix}_max  — numeric range (see _MINMAX_MAP)
        match_types                  — list of str, OR logic within group
        phrases_containing           — comma-separated include terms
        exclude_phrases              — comma-separated exclude terms

    Args:
        df:      Cleaned Cerebro DataFrame (from cerebro_ingestor).
        filters: Dict of filter criteria. Missing keys are ignored.

    Returns:
        Filtered DataFrame (copy).
    """
    mask = pd.Series(True, index=df.index)

    # --- Min/Max numeric filters ---
    for key, col in _MINMAX_MAP.items():
        if col not in df.columns:
            continue

        min_val = filters.get(f"{key}_min")
        if min_val is not None:
            mask &= df[col] >= min_val

        max_val = filters.get(f"{key}_max")
        if max_val is not None:
            mask &= df[col] <= max_val

    # --- Match Type (OR within group) ---
    match_types = filters.get("match_types")
    if match_types:
        type_mask = pd.Series(False, index=df.index)
        for label in match_types:
            col = _MATCH_TYPE_MAP.get(label)
            if col and col in df.columns:
                type_mask |= df[col] > 0
        mask &= type_mask

    # --- Phrases Containing (AND — all terms must appear) ---
    phrases_in = filters.get("phrases_containing", "")
    if phrases_in:
        terms = [t.strip().lower() for t in phrases_in.split(",") if t.strip()]
        kw_lower = df["keyword_phrase"].str.lower()
        for term in terms:
            mask &= kw_lower.str.contains(term, na=False)

    # --- Exclude Phrases (none of the terms may appear) ---
    phrases_out = filters.get("exclude_phrases", "")
    if phrases_out:
        terms = [t.strip().lower() for t in phrases_out.split(",") if t.strip()]
        kw_lower = df["keyword_phrase"].str.lower()
        for term in terms:
            mask &= ~kw_lower.str.contains(term, na=False)

    return df.loc[mask].copy()


# ---------------------------------------------------------------------------
# CLI test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parquet_path = os.path.join(_PROCESSED_DIR, "source_1_cerebro.parquet")
    df = pd.read_parquet(parquet_path)
    total = len(df)

    rules = get_strategy_preset("Tactical")
    rules["sales_min"] = 10

    print(f"Total keywords loaded: {total:,}")
    print(f"Preset rules: {rules}")

    filtered = apply_cerebro_filters(df, rules)
    print(f"Strategy: Tactical | Rows Remaining: {len(filtered):,}")

    print("\n--- Sample (first 5 rows) ---")
    print(
        filtered[["keyword_phrase", "search_volume", "keyword_sales", "word_count"]]
        .head(5)
        .to_string(index=False)
    )
