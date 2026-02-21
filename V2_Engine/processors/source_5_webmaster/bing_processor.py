"""
Source 5 Webmaster — Bing GEO Processor

Python port of the n8n "Bing GEO Strategy Engine" workflow:
    Search Query Engine  → score_queries()
    Page Query Engine    → score_pages()
    Build 7D/28D Report  → build_bing_report()
    Bing Strategy Engine → categorize_bing_strategy()

Public API:
    fetch_bing_query_stats(api_key, site_url)           -> list[dict]
    fetch_bing_page_stats(api_key, site_url, days)      -> list[dict]
    build_bing_report(query_rows, page_rows)            -> dict
    categorize_bing_strategy(report)                    -> dict
"""

from __future__ import annotations

import logging
import re
from datetime import date, datetime, timedelta

import pandas as pd
import requests

logger = logging.getLogger(__name__)

_BING_BASE = "https://ssl.bing.com/webmaster/api.svc/json"

# Commercial intent keywords (mirrors n8n Bing Strategy Engine)
_COMMERCIAL_KEYWORDS = frozenset({
    "buy", "course", "service", "price", "review", "audit",
    "training", "bazaar", "amazon", "guide", "how",
})
# Informational intent hints (AI Citation Score)
_INFO_HINTS = frozenset({
    "how", "what", "why", "guide", "tutorial", "best", "vs",
    "compare", "review", "price", "meaning", "definition", "explain",
})
# Navigational intent hints (lower AI citation potential)
_NAV_HINTS = frozenset({
    "login", "homepage", "official", "site:", "facebook",
    "instagram", "youtube",
})


# ===========================================================================
#  BING API — FETCH
# ===========================================================================

def fetch_bing_query_stats(api_key: str, site_url: str) -> list[dict]:
    """
    Call Bing GetQueryStats (returns all query rows available for the site).
    Returns raw list of row dicts with Bing /Date()/ timestamps.
    """
    if not api_key or not site_url:
        return []
    try:
        resp = requests.get(
            f"{_BING_BASE}/GetQueryStats",
            params={"apikey": api_key, "siteUrl": site_url},
            timeout=15,
        )
        if resp.status_code != 200:
            logger.warning(f"Bing GetQueryStats {resp.status_code}: {resp.text[:200]}")
            return []
        return resp.json().get("d", [])
    except Exception as exc:
        logger.warning(f"fetch_bing_query_stats error: {exc}")
        return []


def fetch_bing_page_stats(api_key: str, site_url: str, days: int = 35) -> list[dict]:
    """
    Call Bing GetPageStats for the past `days` days.
    Returns raw list of row dicts with Bing /Date()/ timestamps.
    days=35 gives enough data for a 28-day A/B window split.
    """
    if not api_key or not site_url:
        return []
    today = date.today()
    start = today - timedelta(days=days)
    try:
        resp = requests.get(
            f"{_BING_BASE}/GetPageStats",
            params={
                "apikey": api_key,
                "siteUrl": site_url,
                "startDate": start.isoformat(),
                "endDate": today.isoformat(),
            },
            timeout=15,
        )
        if resp.status_code != 200:
            logger.warning(f"Bing GetPageStats {resp.status_code}: {resp.text[:200]}")
            return []
        return resp.json().get("d", [])
    except Exception as exc:
        logger.warning(f"fetch_bing_page_stats error: {exc}")
        return []


# ===========================================================================
#  DATE HELPERS
# ===========================================================================

def parse_bing_date(bing_date_str: str) -> str | None:
    """
    Convert Bing /Date(1234567890000+0800)/ → '2025-12-17'.
    Returns None on any failure.
    """
    if not bing_date_str:
        return None
    try:
        m = re.search(r"/Date\((\d+)([+-]\d{4})?\)/", str(bing_date_str))
        if not m:
            return None
        ms = int(m.group(1))
        return datetime.utcfromtimestamp(ms / 1000).strftime("%Y-%m-%d")
    except Exception:
        return None


def _normalize_query_rows(raw_rows: list[dict]) -> pd.DataFrame:
    """Normalize Bing GetQueryStats raw rows → clean DataFrame."""
    records = []
    for r in raw_rows:
        avg_pos = r.get("AvgImpressionPosition")
        records.append({
            "query": r.get("Query", ""),
            "date": parse_bing_date(r.get("Date", "")),
            "clicks": int(r.get("Clicks", 0) or 0),
            "impressions": int(r.get("Impressions", 0) or 0),
            "avgImprPos": None if avg_pos == -1 else (float(avg_pos) if avg_pos else None),
        })
    return pd.DataFrame(records)


def _normalize_page_rows(raw_rows: list[dict]) -> pd.DataFrame:
    """Normalize Bing GetPageStats raw rows → clean DataFrame."""
    records = []
    for r in raw_rows:
        avg_pos = r.get("AvgImpressionPosition")
        page = (r.get("Url") or r.get("URL") or r.get("Page")
                or r.get("page") or r.get("url") or "")
        records.append({
            "page": page,
            "date": parse_bing_date(r.get("Date", "")),
            "clicks": int(r.get("Clicks", 0) or 0),
            "impressions": int(r.get("Impressions", 0) or 0),
            "avgImprPos": None if avg_pos == -1 else (float(avg_pos) if avg_pos else None),
        })
    return pd.DataFrame(records)


# ===========================================================================
#  WINDOW SPLIT  (mirrors n8n windowSplitCalendar)
# ===========================================================================

def window_split(
    df: pd.DataFrame,
    window_days: int,
    date_col: str = "date",
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """
    Calendar-based A/B window split.
        Period A = [today - window_days, today)          ← current period
        Period B = [today - 2*window_days, today - window_days)  ← previous period

    Returns (df_A, df_B, window_meta_dict).
    """
    today = date.today()
    start_a = today - timedelta(days=window_days)
    start_b = today - timedelta(days=window_days * 2)
    end_b = start_a

    df = df.copy()
    df["_d"] = pd.to_datetime(df[date_col], errors="coerce").dt.date
    df_a = df[(df["_d"] >= start_a) & (df["_d"] < today)].drop(columns=["_d"])
    df_b = df[(df["_d"] >= start_b) & (df["_d"] < end_b)].drop(columns=["_d"])

    meta = {
        "A": {"start": start_a.isoformat(), "end": today.isoformat()},
        "B": {"start": start_b.isoformat(), "end": end_b.isoformat()},
    }
    return df_a, df_b, meta


# ===========================================================================
#  GROUPING & SCORING
# ===========================================================================

def _clamp(val: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, val))


def _group_by_key(df: pd.DataFrame, key_col: str) -> pd.DataFrame:
    """Aggregate rows by key_col; compute weighted average position."""
    if df.empty:
        return pd.DataFrame(columns=[key_col, "clicks", "impressions", "avgImprPos", "ctr"])

    df = df.copy()
    df["_wp"] = df.apply(
        lambda r: (r["avgImprPos"] * r["impressions"])
        if (r.get("avgImprPos") is not None and r["impressions"] > 0) else 0.0,
        axis=1,
    )
    grouped = df.groupby(key_col, as_index=False).agg(
        clicks=("clicks", "sum"),
        impressions=("impressions", "sum"),
        _wp_sum=("_wp", "sum"),
        _imp_cnt=("impressions", "count"),
    )
    grouped["avgImprPos"] = grouped.apply(
        lambda r: r["_wp_sum"] / r["impressions"] if r["impressions"] > 0 else None,
        axis=1,
    )
    grouped["ctr"] = grouped.apply(
        lambda r: r["clicks"] / r["impressions"] if r["impressions"] > 0 else 0.0,
        axis=1,
    )
    return grouped.drop(columns=["_wp_sum", "_imp_cnt"])


def _growth_score(
    impr_a: float, impr_b: float,
    click_a: float, click_b: float,
    ctr_a: float,
) -> dict:
    """
    Port of n8n scoreItem(). Returns score (0-100 clamped) + signal flags.
    Weights: impr_growth*55, click_growth*20, low_ctr_bonus*15, new_vis*10
    """
    impr_growth = ((impr_a - impr_b) / impr_b) if impr_b > 0 else (1.0 if impr_a > 0 else 0.0)
    click_growth = ((click_a - click_b) / click_b) if click_b > 0 else (1.0 if click_a > 0 else 0.0)

    g_impr = _clamp((impr_growth + 1) * 50) / 100
    g_click = _clamp((click_growth + 1) * 50) / 100

    low_ctr_bonus = (
        1.0 if (impr_a >= 30 and ctr_a <= 0.01) else
        0.7 if (impr_a >= 50 and ctr_a <= 0.02) else
        0.5 if (impr_a >= 100 and ctr_a <= 0.03) else
        0.0
    )
    new_vis = 1.0 if (impr_b == 0 and impr_a >= 20) else 0.0

    score = _clamp(
        (g_impr * 55) + (g_click * 20) + (low_ctr_bonus * 15) + (new_vis * 10)
    )
    return {
        "score": round(score),
        "impr_growth": round(impr_growth, 4),
        "signals_rising_visibility": bool(impr_growth > 0.2),
        "signals_low_ctr_ai_intent": bool(low_ctr_bonus > 0),
        "signals_new_visibility": bool(new_vis == 1.0),
    }


def _ai_citation_score(query: str, impr_a: float, ctr_a: float, avg_pos) -> dict:
    """
    Port of n8n aiCitationScore(). 4-component GEO signal score (0-100).
    HIGH ≥75, MEDIUM ≥55, LOW <55.
    """
    # Position component (40%)
    if avg_pos is None:
        pos_score = 0.35
    elif avg_pos <= 3:
        pos_score = 1.0
    elif avg_pos <= 6:
        pos_score = 0.75
    elif avg_pos <= 10:
        pos_score = 0.45
    else:
        pos_score = 0.2

    # Low-CTR component (30%) — many impressions but few clicks = AI may answer it
    low_ctr_score = (
        1.0 if (impr_a >= 50 and ctr_a <= 0.02) else
        0.9 if (impr_a >= 30 and ctr_a <= 0.03) else
        0.7 if (impr_a >= 10 and ctr_a <= 0.05) else
        0.2
    )

    # Volume component (20%)
    volume_score = (
        1.0 if impr_a >= 200 else
        0.75 if impr_a >= 80 else
        0.55 if impr_a >= 30 else
        0.35 if impr_a >= 10 else
        0.15
    )

    # Intent component (10%)
    q = str(query).lower()
    if any(h in q for h in _NAV_HINTS):
        intent_score = 0.25
    elif any(h in q for h in _INFO_HINTS):
        intent_score = 0.85
    else:
        intent_score = 0.5

    raw = (pos_score * 40) + (low_ctr_score * 30) + (volume_score * 20) + (intent_score * 10)
    score = round(_clamp(raw))
    tier = "HIGH" if score >= 75 else "MEDIUM" if score >= 55 else "LOW"
    return {"ai_citation_score": score, "ai_citation_tier": tier}


def score_queries(
    group_a: pd.DataFrame,
    group_b: pd.DataFrame,
    key_col: str = "query",
) -> pd.DataFrame:
    """
    Compute Growth Score + AI Citation Score for all entries in group_a.
    group_a/group_b are already aggregated (one row per key).
    Returns sorted DataFrame (highest score first).
    """
    if group_a.empty:
        return pd.DataFrame()

    idx_b = group_b.set_index(key_col) if not group_b.empty else pd.DataFrame()

    records = []
    for _, row_a in group_a.iterrows():
        key = row_a[key_col]
        impr_a = float(row_a["impressions"])
        click_a = float(row_a["clicks"])
        ctr_a = float(row_a.get("ctr", 0.0) or 0.0)
        avg_pos = row_a.get("avgImprPos")

        if not idx_b.empty and key in idx_b.index:
            row_b = idx_b.loc[key]
            impr_b = float(row_b["impressions"])
            click_b = float(row_b["clicks"])
        else:
            impr_b, click_b = 0.0, 0.0

        gs = _growth_score(impr_a, impr_b, click_a, click_b, ctr_a)
        acs = _ai_citation_score(key, impr_a, ctr_a, avg_pos)

        records.append({
            key_col: key,
            "clicks_a": click_a,
            "impressions_a": impr_a,
            "ctr_a": round(ctr_a * 100, 2),   # as percentage
            "clicks_b": click_b,
            "impressions_b": impr_b,
            "avgImprPos": round(avg_pos, 2) if avg_pos is not None else None,
            **gs,
            **acs,
        })

    return pd.DataFrame(records).sort_values("score", ascending=False).reset_index(drop=True)


def score_pages(group_a: pd.DataFrame, group_b: pd.DataFrame) -> pd.DataFrame:
    """Same scoring logic applied to page-level data (key_col='page')."""
    return score_queries(group_a, group_b, key_col="page")


# ===========================================================================
#  REPORT BUILDER  (mirrors n8n Build 7D/28D Report nodes)
# ===========================================================================

def _build_window_report(
    scored: pd.DataFrame,
    key_col: str,
    report_type: str,
    window_meta: dict,
) -> dict:
    """Build one period report from a scored DataFrame."""
    empty_sections = {
        ("top_queries" if key_col == "query" else "top_pages"): [],
        "rising_visibility": [],
        "low_ctr_opportunities": [],
        "new_visibility": [],
    }
    if scored.empty:
        return {
            "report_type": report_type,
            "window": window_meta,
            "totals": {"clicks": 0, "impressions": 0, "ctr": "0.0%"},
            "sections": empty_sections,
        }

    total_clicks = int(scored["clicks_a"].sum())
    total_impr = int(scored["impressions_a"].sum())
    total_ctr = f"{(total_clicks / total_impr * 100):.1f}%" if total_impr else "0.0%"

    top_key = "top_queries" if key_col == "query" else "top_pages"
    top_cols = [c for c in [key_col, "clicks_a", "impressions_a", "ctr_a", "avgImprPos", "score"]
                if c in scored.columns]

    rising = scored[scored["signals_rising_visibility"] == True]  # noqa: E712
    new_vis = scored[scored["signals_new_visibility"] == True]    # noqa: E712
    low_ctr_mask = (scored["impressions_a"] >= 10) & (scored["ctr_a"] <= 2.0)  # ctr_a is % here
    low_ctr = scored[low_ctr_mask].copy()
    if not low_ctr.empty:
        low_ctr["recommended_fix"] = (
            "Improve title/H1 alignment + add FAQ/Q&A block + strengthen internal links"
        )

    def safe_records(df, cols):
        present = [c for c in cols if c in df.columns]
        return df[present].head(15).to_dict("records")

    return {
        "report_type": report_type,
        "window": window_meta,
        "totals": {"clicks": total_clicks, "impressions": total_impr, "ctr": total_ctr},
        "sections": {
            top_key: safe_records(scored, top_cols),
            "rising_visibility": safe_records(
                rising, [key_col, "impressions_a", "ctr_a", "avgImprPos", "score"]
            ),
            "low_ctr_opportunities": safe_records(
                low_ctr, [key_col, "impressions_a", "ctr_a", "avgImprPos", "recommended_fix"]
            ),
            "new_visibility": safe_records(
                new_vis, [key_col, "impressions_a", "avgImprPos"]
            ),
        },
    }


def build_bing_report(query_rows: list[dict], page_rows: list[dict]) -> dict:
    """
    Full pipeline: normalize → window-split → group → score → build 4 reports.

    Returns dict with keys:
        query_7d, query_28d  — BING_QUERY_REPORT_7D / 28D
        page_7d,  page_28d   — BING_PAGE_REPORT_7D  / 28D
    """
    # --- Query track ---
    q_df = _normalize_query_rows(query_rows) if query_rows else pd.DataFrame()
    reports: dict = {}

    for days, suffix in [(7, "7d"), (28, "28d")]:
        if not q_df.empty and "date" in q_df.columns:
            q_a, q_b, q_win = window_split(q_df, days)
            ga = _group_by_key(q_a, "query")
            gb = _group_by_key(q_b, "query")
            scored_q = score_queries(ga, gb)
        else:
            scored_q = pd.DataFrame()
            today = date.today()
            q_win = {
                "A": {"start": (today - timedelta(days=days)).isoformat(), "end": today.isoformat()},
                "B": {"start": (today - timedelta(days=days * 2)).isoformat(),
                      "end": (today - timedelta(days=days)).isoformat()},
            }

        reports[f"query_{suffix}"] = _build_window_report(
            scored_q, "query", f"BING_QUERY_REPORT_{suffix.upper()}", q_win,
        )

    # --- Page track ---
    p_df = _normalize_page_rows(page_rows) if page_rows else pd.DataFrame()

    for days, suffix in [(7, "7d"), (28, "28d")]:
        if not p_df.empty and "date" in p_df.columns:
            p_a, p_b, p_win = window_split(p_df, days)
            pa = _group_by_key(p_a, "page")
            pb = _group_by_key(p_b, "page")
            scored_p = score_pages(pa, pb)
        else:
            scored_p = pd.DataFrame()
            today = date.today()
            p_win = {
                "A": {"start": (today - timedelta(days=days)).isoformat(), "end": today.isoformat()},
                "B": {"start": (today - timedelta(days=days * 2)).isoformat(),
                      "end": (today - timedelta(days=days)).isoformat()},
            }

        reports[f"page_{suffix}"] = _build_window_report(
            scored_p, "page", f"BING_PAGE_REPORT_{suffix.upper()}", p_win,
        )

    return reports


# ===========================================================================
#  BING STRATEGY ENGINE  (mirrors n8n Bing Strategy Engine node)
# ===========================================================================

def categorize_bing_strategy(report: dict) -> dict:
    """
    Categorize 7-day queries into three strategic buckets.

    GEO Opportunities  — impressions > 0 AND clicks == 0
                         (Zero click = AI may be answering this query)
    Commercial Wins    — query contains commercial intent keywords
    Early Signals      — everything else (all queries, no threshold)
    """
    q7_sections = report.get("query_7d", {}).get("sections", {})
    all_q7 = q7_sections.get("top_queries", [])

    geo, commercial, early = [], [], []

    for item in all_q7:
        query = str(item.get("query", "")).lower()
        impr = float(item.get("impressions_a", item.get("impressions", 0)) or 0)
        clicks = float(item.get("clicks_a", item.get("clicks", 0)) or 0)
        pos = item.get("avgImprPos")

        is_commercial = any(k in query for k in _COMMERCIAL_KEYWORDS)
        is_geo = impr > 0 and clicks == 0

        if is_geo:
            geo.append({
                "query": item.get("query", ""),
                "position": round(float(pos), 1) if pos is not None else None,
                "impressions_7d": int(impr),
                "insight": (
                    f"Rank #{round(float(pos)) if pos else '?'} — "
                    "Zero clicks (Potential AI Answer)"
                ),
            })
        elif is_commercial:
            commercial.append({
                "query": item.get("query", ""),
                "trend": "UP" if item.get("signals_rising_visibility") else "Stable",
                "stats": f"{int(impr)} impr",
                "score": item.get("score", 0),
            })
        else:
            early.append({
                "query": item.get("query", ""),
                "stats": f"{int(impr)} impr (Pos {round(float(pos)) if pos else '?'})",
            })

    return {
        "geo_opportunities": geo,
        "commercial_wins": commercial,
        "early_signals": early,
    }
