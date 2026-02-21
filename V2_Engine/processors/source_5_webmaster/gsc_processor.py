"""
Source 5 Webmaster — GSC Data Processor

Python port of the n8n "GSC Data Processor" JavaScript code node
(from AnergyAcademy 7 Days Compare (GSC).json and 28 Days Compare (GSC).json).

Public API:
    fetch_gsc_comparison(service, site_url, window_days) -> list[dict]
    process_gsc_rows(rows)                               -> dict
    is_low_traffic(processed, threshold)                 -> bool
"""

from __future__ import annotations

import logging
from datetime import date, timedelta

import pandas as pd

logger = logging.getLogger(__name__)

# Mirrors n8n thresholds
_IMPRESSION_THRESHOLD = 10
_POSITION_THRESHOLD = 1.0
_LOW_TRAFFIC_THRESHOLD = 100


# ---------------------------------------------------------------------------
# GSC API — Fetch
# ---------------------------------------------------------------------------

def fetch_gsc_comparison(service, site_url: str, window_days: int) -> list[dict]:
    """
    Call GSC searchanalytics().query() with a two-period comparison body.

    For 7-day:  dimensions = [page, query, date]  — daily rows, aggregated below
    For 28-day: dimensions = [page, query]         — GSC pre-aggregates (no date)

    The GSC API returns both periods when dateRanges has two entries:
        row["clicks"]              = Period A clicks
        row["clicksCompared"]      = Period B clicks
        row["impressions"]         = Period A impressions
        row["impressionsCompared"] = Period B impressions
        row["position"]            = Period A avg position
        row["positionCompared"]    = Period B avg position

    Returns list of row dicts matching the n8n row schema.
    """
    today = date.today()
    start_a = today - timedelta(days=window_days)
    end_a = today
    start_b = today - timedelta(days=window_days * 2)
    end_b = today - timedelta(days=window_days)

    dims = ["page", "query", "date"] if window_days <= 7 else ["page", "query"]

    body = {
        "startDate": start_a.isoformat(),
        "endDate": end_a.isoformat(),
        "dimensions": dims,
        "rowLimit": 10000,
        "type": "web",
        "dateRanges": [
            {"startDate": start_a.isoformat(), "endDate": end_a.isoformat()},
            {"startDate": start_b.isoformat(), "endDate": end_b.isoformat()},
        ],
    }

    try:
        response = service.searchanalytics().query(
            siteUrl=site_url, body=body
        ).execute()
    except Exception as exc:
        logger.warning(f"GSC API call failed: {exc}")
        return []

    range_a = {"startDate": start_a.isoformat(), "endDate": end_a.isoformat()}
    range_b = {"startDate": start_b.isoformat(), "endDate": end_b.isoformat()}

    rows_out = []
    for row in response.get("rows", []):
        keys = row.get("keys", [])
        page = keys[0] if len(keys) > 0 else ""
        query = keys[1] if len(keys) > 1 else ""
        date_val = keys[2] if len(keys) > 2 else None

        rows_out.append({
            "page": page,
            "query": query,
            "date": date_val,
            "clicks_a": float(row.get("clicks", 0) or 0),
            "clicks_b": float(row.get("clicksCompared", 0) or 0),
            "impr_a": float(row.get("impressions", 0) or 0),
            "impr_b": float(row.get("impressionsCompared", 0) or 0),
            "pos_a": float(row.get("position", 0) or 0),
            "pos_b": float(row.get("positionCompared", 0) or 0),
            "range_a": range_a,
            "range_b": range_b,
        })

    return rows_out


# ---------------------------------------------------------------------------
# GSC Data Processor — Core Algorithm
# ---------------------------------------------------------------------------

def process_gsc_rows(rows: list[dict]) -> dict:
    """
    Python port of the n8n "GSC Data Processor" JS code node.

    Aggregates daily rows by query, computes impression-weighted average
    position, derives diff fields, and classifies into 5 buckets:
        new_keywords, lost_keywords, rising_keywords,
        declining_keywords, page_two_opportunities

    Input rows: list of dicts with keys
        query, page, clicks_a, clicks_b, impr_a, impr_b, pos_a, pos_b,
        range_a (dict), range_b (dict)

    Returns:
        {
            "summary": {...},
            "new_keywords": [...],
            "lost_keywords": [...],
            "rising_keywords": [...],
            "declining_keywords": [...],
            "page_two_opportunities": [...]
        }
    """
    if not rows:
        return _empty_result()

    df = pd.DataFrame(rows)

    for col in ["clicks_a", "clicks_b", "impr_a", "impr_b", "pos_a", "pos_b"]:
        df[col] = pd.to_numeric(df.get(col, 0), errors="coerce").fillna(0.0)

    # --- STEP 1: Aggregate by query ---
    # Weighted position helpers: pos * impr (mirrors n8n impr_pos_sum)
    df["_wp_a"] = df["pos_a"] * df["impr_a"]
    df["_wp_b"] = df["pos_b"] * df["impr_b"]

    grouped = df.groupby("query", as_index=False).agg(
        total_clicks_a=("clicks_a", "sum"),
        total_clicks_b=("clicks_b", "sum"),
        total_impr_a=("impr_a", "sum"),
        total_impr_b=("impr_b", "sum"),
        _wp_a_sum=("_wp_a", "sum"),
        _wp_b_sum=("_wp_b", "sum"),
    )

    # Collect unique pages per query
    pages_agg = (
        df.groupby("query")["page"]
        .apply(lambda x: list(x.dropna().unique()))
        .reset_index()
        .rename(columns={"page": "pages"})
    )
    grouped = grouped.merge(pages_agg, on="query", how="left")

    # --- STEP 2: Derived fields ---
    # Weighted average position (mirrors n8n: impr_pos_sum / total_impr)
    grouped["avg_pos_a"] = grouped.apply(
        lambda r: round(r["_wp_a_sum"] / r["total_impr_a"], 2)
        if r["total_impr_a"] > 0 else 0.0,
        axis=1,
    )
    grouped["avg_pos_b"] = grouped.apply(
        lambda r: round(r["_wp_b_sum"] / r["total_impr_b"], 2)
        if r["total_impr_b"] > 0 else 0.0,
        axis=1,
    )
    grouped["impr_diff"] = grouped["total_impr_a"] - grouped["total_impr_b"]
    grouped["clicks_diff"] = grouped["total_clicks_a"] - grouped["total_clicks_b"]
    grouped["pos_diff"] = grouped.apply(
        lambda r: round(r["avg_pos_a"] - r["avg_pos_b"], 2)
        if r["avg_pos_a"] > 0 and r["avg_pos_b"] > 0 else 0.0,
        axis=1,
    )
    grouped = grouped.drop(columns=["_wp_a_sum", "_wp_b_sum"])

    # --- STEP 3: Categorize (mirrors n8n boolean logic) ---
    mask_new = (grouped["total_impr_b"] == 0) & (grouped["total_impr_a"] > 0)
    mask_lost = (grouped["total_impr_a"] == 0) & (grouped["total_impr_b"] > 0)
    mask_both = (grouped["total_impr_a"] > 0) & (grouped["total_impr_b"] > 0)

    mask_rising = (
        mask_both
        & (grouped["impr_diff"] > _IMPRESSION_THRESHOLD)
        & (grouped["pos_diff"] < -_POSITION_THRESHOLD)
    )
    mask_declining = (
        mask_both
        & (grouped["impr_diff"] < -_IMPRESSION_THRESHOLD)
        & (grouped["pos_diff"] > _POSITION_THRESHOLD)
    )
    # Page Two: pos 10.1–20 (mirrors n8n: avg_pos_a > 10 && avg_pos_a <= 20)
    mask_page2 = (grouped["avg_pos_a"] > 10) & (grouped["avg_pos_a"] <= 20)

    new_kw = grouped[mask_new].sort_values("total_impr_a", ascending=False)
    lost_kw = grouped[mask_lost].sort_values("total_impr_b", ascending=False)
    rising_kw = grouped[mask_rising].sort_values("impr_diff", ascending=False)
    declining_kw = grouped[mask_declining].sort_values("impr_diff", ascending=True)
    page2_kw = grouped[mask_page2].sort_values("total_impr_a", ascending=False)

    # --- STEP 4: Summary ---
    summary = {
        "total_clicks_a": int(grouped["total_clicks_a"].sum()),
        "total_clicks_b": int(grouped["total_clicks_b"].sum()),
        "total_impr_a": int(grouped["total_impr_a"].sum()),
        "total_impr_b": int(grouped["total_impr_b"].sum()),
        "new_keyword_count": int(mask_new.sum()),
        "lost_keyword_count": int(mask_lost.sum()),
        "rising_keyword_count": int(mask_rising.sum()),
        "declining_keyword_count": int(mask_declining.sum()),
        "page_two_opportunities_count": int(mask_page2.sum()),
        "range_a": rows[0].get("range_a", {}),
        "range_b": rows[0].get("range_b", {}),
    }

    return {
        "summary": summary,
        "new_keywords": new_kw.to_dict("records"),
        "lost_keywords": lost_kw.to_dict("records"),
        "rising_keywords": rising_kw.to_dict("records"),
        "declining_keywords": declining_kw.to_dict("records"),
        "page_two_opportunities": page2_kw.to_dict("records"),
    }


def is_low_traffic(processed: dict, threshold: int = _LOW_TRAFFIC_THRESHOLD) -> bool:
    """
    Traffic Check Gate — mirrors the n8n IF node logic.

    Returns True  → Low Traffic mode → Content Suggestions branch
    Returns False → Normal mode      → Full SEO Report branch

    Condition (OR): total_impr_a < threshold  OR  new_keyword_count == 0
    """
    summary = processed.get("summary", {})
    return (
        summary.get("total_impr_a", 0) < threshold
        or summary.get("new_keyword_count", 0) == 0
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _empty_result() -> dict:
    return {
        "summary": {
            "total_clicks_a": 0, "total_clicks_b": 0,
            "total_impr_a": 0, "total_impr_b": 0,
            "new_keyword_count": 0, "lost_keyword_count": 0,
            "rising_keyword_count": 0, "declining_keyword_count": 0,
            "page_two_opportunities_count": 0,
            "range_a": {}, "range_b": {},
        },
        "new_keywords": [],
        "lost_keywords": [],
        "rising_keywords": [],
        "declining_keywords": [],
        "page_two_opportunities": [],
    }
