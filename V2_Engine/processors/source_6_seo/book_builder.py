"""
Book Builder — Epic 0 Data Assembly Engine.

Reads raw export files (demo mode) or KB storage (live mode) and assembles
the canonical "Book" JSON bundle consumed by the Source 6 Writer Engine.

Usage:
    from V2_Engine.processors.source_6_seo.book_builder import build_book

    book = build_book(
        product_slug="baby_spoon",
        site_domain="anergyacademy.com",
        mode="demo",          # "demo" | "live"
    )

Modes:
    demo — reads from data/raw_zeabur_exports/ using source-specific glob patterns
    live — reads from V2_Engine/knowledge_base/storage/{source_folder}/ (latest file)
"""

from __future__ import annotations

import glob
import json
import os
import re
from datetime import datetime

import pandas as pd

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------
_PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )
    )
)
_RAW_EXPORT_DIR = os.path.join(_PROJECT_ROOT, "data", "raw_zeabur_exports")
_KB_STORAGE_DIR = os.path.join(_PROJECT_ROOT, "V2_Engine", "knowledge_base", "storage")

# KB subfolder names per source
_KB_FOLDERS = {
    "catalog":    "0_catalog_insight",
    "traffic":    "1_keyword_traffic",
    "reviews":    "2_review_analysis",
    "rufus":      "3_rufus_defense",
    "webmaster":  "5_webmaster",
}


# ===========================================================================
# PUBLIC API
# ===========================================================================

def build_book(
    product_slug: str,
    site_domain: str,
    mode: str = "demo",
) -> dict:
    """
    Master assembler. Calls all 5 source builders and returns the canonical Book JSON.

    Args:
        product_slug: snake_case product identifier, e.g. "baby_spoon"
        site_domain:  website domain for webmaster data, e.g. "anergyacademy.com"
        mode:         "demo" reads from raw_zeabur_exports/
                      "live" reads from knowledge_base/storage/
    Returns:
        Canonical Book dict with 5 top-level source keys + meta.
    """
    return {
        "meta": {
            "product_slug": product_slug,
            "site_domain": site_domain,
            "mode": mode,
            "built_at": datetime.now().isoformat(),
        },
        "catalog_book":   _build_catalog_book(mode, product_slug),
        "traffic_book":   _build_traffic_book(mode, product_slug),
        "reviews_book":   _build_reviews_book(mode, product_slug),
        "rufus_book":     _build_rufus_book(mode, product_slug),
        "webmaster_book": _build_webmaster_book(mode, site_domain),
    }


# ===========================================================================
# SOURCE BUILDERS (private)
# ===========================================================================

def _build_catalog_book(mode: str, product_slug: str) -> dict:
    """Parses catalog CSV (top_asins, revenue_leaders) + MD regex (market_summary)."""
    result = {
        "status": "ok",
        "top_asins": [],
        "revenue_leaders": [],
        "market_summary": {},
    }

    # --- Locate files ---
    if mode == "demo":
        csv_path = _find_latest_file(_RAW_EXPORT_DIR, f"*catalog*.csv")
        md_path  = _find_latest_file(_RAW_EXPORT_DIR, f"*catalog*.md")
    else:
        folder = os.path.join(_KB_STORAGE_DIR, _KB_FOLDERS["catalog"])
        csv_path = _find_latest_file(folder, "*.csv")
        md_path  = _find_latest_file(folder, "*.md")

    # --- Parse CSV ---
    if csv_path and os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path, encoding="utf-8")

            asin_col    = _find_col(df, ["ASIN", "asin"])
            brand_col   = _find_col(df, ["Brand", "brand"])
            price_col   = _find_col(df, ["Price  US$", "Price US$", "Price", "price"])
            rev_col     = _find_col(df, ["Parent Level Revenue", "parent_level_revenue"])
            bsr_col     = _find_col(df, ["BSR", "bsr"])
            rating_col  = _find_col(df, ["Ratings", "Rating", "ratings", "rating"])
            rcount_col  = _find_col(df, ["Review Count", "review_count"])

            rows = []
            for _, row in df.iterrows():
                entry = {
                    "asin":           _safe_str(row, asin_col),
                    "brand":          _safe_str(row, brand_col),
                    "price":          _safe_float(row, price_col),
                    "parent_revenue": _safe_float(row, rev_col),
                    "bsr":            _safe_float(row, bsr_col),
                    "rating":         _safe_float(row, rating_col),
                    "review_count":   _safe_float(row, rcount_col),
                }
                if entry["asin"]:
                    rows.append(entry)

            # Dedupe by ASIN
            seen = set()
            deduped = []
            for r in rows:
                if r["asin"] not in seen:
                    seen.add(r["asin"])
                    deduped.append(r)

            result["top_asins"] = deduped

            # Revenue leaders: top 10 by parent_revenue DESC
            sorted_rows = sorted(
                [r for r in deduped if r["parent_revenue"] is not None],
                key=lambda x: x["parent_revenue"],
                reverse=True,
            )
            result["revenue_leaders"] = sorted_rows[:10]

        except Exception as e:
            result["status"] = f"csv_error: {e}"

    # --- Parse MD for aggregate stats ---
    if md_path and os.path.exists(md_path):
        try:
            with open(md_path, "r", encoding="utf-8") as f:
                md_text = f.read()
            result["market_summary"] = _parse_catalog_md_stats(md_text)
        except Exception as e:
            result["market_summary"] = {"error": str(e)}

    return result


def _build_traffic_book(mode: str, product_slug: str) -> dict:
    """Parses Cerebro CSV. Returns top_keywords, content_gaps, trending, summary."""
    result = {
        "status": "ok",
        "top_keywords": [],
        "content_gaps": [],
        "trending": [],
        "summary": {},
    }

    if mode == "demo":
        csv_path = _find_latest_file(_RAW_EXPORT_DIR, "*cerebro*.csv") \
                   or _find_latest_file(_RAW_EXPORT_DIR, "*traffic*.csv")
    else:
        folder = os.path.join(_KB_STORAGE_DIR, _KB_FOLDERS["traffic"])
        csv_path = _find_latest_file(folder, "*.csv")

    if not csv_path or not os.path.exists(csv_path):
        result["status"] = "no_data"
        return result

    try:
        df = pd.read_csv(csv_path, encoding="utf-8")

        keywords = []
        for _, row in df.iterrows():
            kw = _safe_str(row, "keyword_phrase")
            if not kw:
                continue
            keywords.append({
                "keyword":       kw,
                "volume":        _safe_int(row, "search_volume"),
                "trend":         _safe_int(row, "search_volume_trend"),
                "iq_score":      _safe_float(row, "cerebro_iq_score"),
                "keyword_sales": _safe_int(row, "keyword_sales"),
                "is_organic":    bool(_safe_int(row, "organic")),
                "word_count":    _safe_int(row, "word_count"),
                "cpr":           _safe_int(row, "cpr"),
                "competing_products": _safe_int(row, "competing_products"),
            })

        # Sort by volume DESC
        keywords.sort(key=lambda x: (x["volume"] or 0), reverse=True)

        result["top_keywords"] = keywords
        result["content_gaps"] = [k for k in keywords if not k["is_organic"]]
        result["trending"] = [k for k in keywords if (k["trend"] or 0) >= 20]

        result["summary"] = {
            "total_keywords": len(keywords),
            "organic_count":  sum(1 for k in keywords if k["is_organic"]),
            "gap_count":      sum(1 for k in keywords if not k["is_organic"]),
            "trending_count": len(result["trending"]),
        }

    except Exception as e:
        result["status"] = f"csv_error: {e}"

    return result


def _build_reviews_book(mode: str, product_slug: str) -> dict:
    """Parses review CSV with secondary blob parsing. Returns happy/defect themes."""
    result = {
        "status": "ok",
        "happy_themes": [],
        "defect_themes": [],
        "cosmo_intents": [],
        "eeat_proof": [],
        "rufus_keywords": [],
        "competitor_wins": [],
        "summary": {},
    }

    if mode == "demo":
        csv_path = _find_latest_file(_RAW_EXPORT_DIR, "*review*.csv")
    else:
        folder = os.path.join(_KB_STORAGE_DIR, _KB_FOLDERS["reviews"])
        csv_path = _find_latest_file(folder, "*.csv")

    if not csv_path or not os.path.exists(csv_path):
        result["status"] = "no_data"
        return result

    try:
        df = pd.read_csv(csv_path, encoding="utf-8")

        all_happy_themes = []
        all_defect_themes = []
        all_cosmo: list[str] = []
        all_eeat: list[dict] = []
        all_rufus_kw: list[str] = []
        all_comp_wins: list[str] = []
        asin_set: set[str] = set()

        for _, row in df.iterrows():
            report_type = _safe_str(row, "report_type") or ""
            asin = _safe_str(row, "asin") or ""
            if asin:
                asin_set.add(asin)

            # Buying factors
            raw_bf = _safe_str(row, "buying_factors") or ""
            factors = _parse_buying_factors(raw_bf)

            if report_type == "happy":
                all_happy_themes.extend(factors)
            elif report_type == "defect":
                all_defect_themes.extend(factors)

            # COSMO intents — deduplicated union
            raw_cosmo = _safe_str(row, "cosmo_intents") or ""
            for line in raw_cosmo.split("\n"):
                intent = line.strip().lstrip("- ").strip()
                if intent:
                    all_cosmo.append(intent)

            # EEAT proof blocks
            raw_eeat = _safe_str(row, "eeat_stories") or ""
            all_eeat.extend(_parse_eeat_blocks(raw_eeat))

            # Rufus keywords — comma-separated
            raw_kw = _safe_str(row, "rufus_keywords") or ""
            for kw in raw_kw.split(","):
                kw = kw.strip()
                if kw:
                    all_rufus_kw.append(kw)

            # Competitor wins
            raw_cw = _safe_str(row, "competitor_wins") or ""
            for line in raw_cw.split("\n"):
                cw = line.strip().lstrip("- ").strip()
                if cw:
                    all_comp_wins.append(cw)

        # Aggregate and deduplicate
        result["happy_themes"]   = _aggregate_themes(all_happy_themes)
        result["defect_themes"]  = _aggregate_themes(all_defect_themes)
        result["cosmo_intents"]  = list(dict.fromkeys(all_cosmo))   # preserve order, dedupe
        result["eeat_proof"]     = all_eeat
        result["rufus_keywords"] = list(dict.fromkeys(all_rufus_kw))
        result["competitor_wins"] = list(dict.fromkeys(all_comp_wins))

        result["summary"] = {
            "asin_count":       len(asin_set),
            "happy_theme_count": len(result["happy_themes"]),
            "defect_theme_count": len(result["defect_themes"]),
            "cosmo_intent_count": len(result["cosmo_intents"]),
            "has_defect_data":  len(result["defect_themes"]) > 0,
        }

    except Exception as e:
        result["status"] = f"csv_error: {e}"

    return result


def _build_rufus_book(mode: str, product_slug: str) -> dict:
    """Parses rufus CSV by Source column filter."""
    result = {
        "status": "ok",
        "trap_questions": [],
        "dealbreakers": [],
        "hero_scenarios": [],
        "listing_gaps": [],
        "seo_flags": [],
        "summary": {},
        "listing_coverage_score": None,
    }

    if mode == "demo":
        csv_path = _find_latest_file(_RAW_EXPORT_DIR, "*rufus*.csv")
        md_path  = _find_latest_file(_RAW_EXPORT_DIR, "*rufus*.md")
    else:
        folder = os.path.join(_KB_STORAGE_DIR, _KB_FOLDERS["rufus"])
        csv_path = _find_latest_file(folder, "*.csv")
        md_path  = _find_latest_file(folder, "*.md")

    if not csv_path or not os.path.exists(csv_path):
        result["status"] = "no_data"
        return result

    try:
        df = pd.read_csv(csv_path, encoding="utf-8")

        for _, row in df.iterrows():
            source = _safe_str(row, "Source") or ""
            typ    = _safe_str(row, "Type") or ""
            issue  = _safe_str(row, "Issue") or ""
            detail = _safe_str(row, "Detail") or ""

            src_lower = source.lower()

            if src_lower.startswith("red team"):
                result["trap_questions"].append({
                    "question": issue,
                    "type":     typ,
                    "detail":   detail,
                })
            elif "yellow" in src_lower and "dealbreaker" in src_lower:
                result["dealbreakers"].append({
                    "severity": typ,
                    "issue":    issue,
                    "detail":   detail,
                })
            elif "yellow" in src_lower and "hero" in typ.lower():
                result["hero_scenarios"].append({
                    "scenario": issue,
                    "detail":   detail,
                })
            elif "orange" in src_lower and "listing gap" in src_lower:
                result["listing_gaps"].append({
                    "priority": typ,
                    "gap":      issue,
                    "fix":      detail,
                })
            elif "orange" in src_lower and "seo flag" in src_lower:
                result["seo_flags"].append({
                    "severity": typ,
                    "flag":     issue,
                    "detail":   detail,
                })

        result["summary"] = {
            "trap_count":       len(result["trap_questions"]),
            "dealbreaker_count": len(result["dealbreakers"]),
            "hero_count":       len(result["hero_scenarios"]),
            "gap_count":        len(result["listing_gaps"]),
            "seo_flag_count":   len(result["seo_flags"]),
        }

    except Exception as e:
        result["status"] = f"csv_error: {e}"

    # Coverage score from MD
    if md_path and os.path.exists(md_path):
        try:
            with open(md_path, "r", encoding="utf-8") as f:
                md_text = f.read()
            m = re.search(
                r"[Ll]isting\s+[Cc]overage\s+[Ss]core[:\s]+(\d+)/(\d+)", md_text
            )
            if m:
                result["listing_coverage_score"] = f"{m.group(1)}/{m.group(2)}"
        except Exception:
            pass

    return result


def _build_webmaster_book(mode: str, site_domain: str) -> dict:
    """Loads GSC 7d + 28d + Bing JSON files and merges into unified schema."""
    result = {
        "status": "ok",
        "gsc": {
            "summary": {},
            "new_keywords": [],
            "rising_keywords": [],
            "declining_keywords": [],
            "page_two_opportunities": [],
            "new_keywords_7d": [],
        },
        "bing": {
            "top_queries": [],
            "rising_visibility": [],
            "low_ctr_opportunities": [],
            "top_pages": [],
            "totals_7d": {},
            "totals_28d": {},
        },
        "geo_signals": [],
        "summary": {},
    }

    # --- Locate files ---
    if mode == "demo":
        base_dir = _RAW_EXPORT_DIR
        # Bing: match by site_domain (not product_slug)
        bing_path  = _find_latest_file(base_dir, f"*{site_domain}*bing*.json") \
                     or _find_latest_file(base_dir, "*bing*.json")
        gsc_28_path = _find_latest_file(base_dir, f"*{site_domain}*gsc_28d*.json") \
                      or _find_latest_file(base_dir, "*gsc_28d*.json")
        gsc_7_path  = _find_latest_file(base_dir, f"*{site_domain}*gsc_7d*.json") \
                      or _find_latest_file(base_dir, "*gsc_7d*.json")
    else:
        folder = os.path.join(_KB_STORAGE_DIR, _KB_FOLDERS["webmaster"])
        bing_path   = _find_latest_file(folder, "*bing*.json")
        gsc_28_path = _find_latest_file(folder, "*gsc_28d*.json")
        gsc_7_path  = _find_latest_file(folder, "*gsc_7d*.json")

    any_data = False

    # --- Parse GSC 28d (primary) ---
    if gsc_28_path and os.path.exists(gsc_28_path):
        try:
            with open(gsc_28_path, "r", encoding="utf-8") as f:
                gsc28 = json.load(f)
            result["gsc"]["summary"] = gsc28.get("summary", {})
            result["gsc"]["new_keywords"] = sorted(
                gsc28.get("new_keywords", []),
                key=lambda x: x.get("total_impr_a", 0),
                reverse=True,
            )
            result["gsc"]["rising_keywords"]        = gsc28.get("rising_keywords", [])
            result["gsc"]["declining_keywords"]     = gsc28.get("declining_keywords", [])
            result["gsc"]["page_two_opportunities"] = gsc28.get("page_two_opportunities", [])
            any_data = True
        except Exception as e:
            result["gsc"]["error"] = str(e)

    # --- Parse GSC 7d (velocity signal) ---
    if gsc_7_path and os.path.exists(gsc_7_path):
        try:
            with open(gsc_7_path, "r", encoding="utf-8") as f:
                gsc7 = json.load(f)
            result["gsc"]["new_keywords_7d"] = gsc7.get("new_keywords", [])
            any_data = True
        except Exception as e:
            result["gsc"]["error_7d"] = str(e)

    # --- Parse Bing ---
    if bing_path and os.path.exists(bing_path):
        try:
            with open(bing_path, "r", encoding="utf-8") as f:
                bing = json.load(f)

            report = bing.get("report", {})
            strategy = bing.get("strategy", {})

            q28 = report.get("query_28d", {})
            q7  = report.get("query_7d", {})
            p28 = report.get("page_28d", {})

            secs28 = q28.get("sections", {})
            secp28 = p28.get("sections", {})

            result["bing"]["top_queries"] = sorted(
                secs28.get("top_queries", []),
                key=lambda x: x.get("score", 0),
                reverse=True,
            )
            result["bing"]["rising_visibility"]    = secs28.get("rising_visibility", [])
            result["bing"]["low_ctr_opportunities"] = secs28.get("low_ctr_opportunities", [])
            result["bing"]["top_pages"]            = secp28.get("top_pages", [])
            result["bing"]["totals_7d"]            = q7.get("totals", {})
            result["bing"]["totals_28d"]           = q28.get("totals", {})

            # GEO signals — pre-computed by Source 5
            result["geo_signals"] = strategy.get("geo_opportunities", [])
            any_data = True
        except Exception as e:
            result["bing"]["error"] = str(e)

    if not any_data:
        result["status"] = "no_data"
        result["message"] = (
            "Webmaster data not available. Connect Google Search Console "
            "and Bing in Source 5 to enable."
        )

    # Summary
    result["summary"] = {
        "gsc_new_keywords_28d":  len(result["gsc"]["new_keywords"]),
        "gsc_new_keywords_7d":   len(result["gsc"]["new_keywords_7d"]),
        "gsc_page_two_count":    len(result["gsc"]["page_two_opportunities"]),
        "bing_top_queries":      len(result["bing"]["top_queries"]),
        "geo_signal_count":      len(result["geo_signals"]),
    }

    return result


# ===========================================================================
# HELPER FUNCTIONS (private)
# ===========================================================================

def _find_latest_file(directory: str, pattern: str) -> str | None:
    """
    Glob directory for files matching pattern.
    Returns path of most recently modified match, or None.
    """
    if not os.path.isdir(directory):
        return None
    matches = glob.glob(os.path.join(directory, pattern))
    if not matches:
        return None
    return max(matches, key=os.path.getmtime)


def _find_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """Case-insensitive column lookup. Returns first matching column name."""
    col_lower = {c.lower().strip(): c for c in df.columns}
    for cand in candidates:
        # Try exact match first
        if cand in df.columns:
            return cand
        # Try stripped lowercase
        key = cand.lower().strip()
        if key in col_lower:
            return col_lower[key]
    return None


def _safe_str(row: pd.Series, col: str | None) -> str | None:
    """Return string value from row, None if col missing or NaN."""
    if col is None or col not in row.index:
        return None
    val = row[col]
    if pd.isna(val):
        return None
    return str(val).strip()


def _safe_float(row: pd.Series, col: str | None) -> float | None:
    """Return float value from row, stripping $ and commas. None if missing."""
    if col is None or col not in row.index:
        return None
    val = row[col]
    if pd.isna(val):
        return None
    try:
        cleaned = str(val).replace("$", "").replace(",", "").strip()
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def _safe_int(row: pd.Series, col: str | None) -> int | None:
    """Return int value from row. None if missing or unparseable."""
    f = _safe_float(row, col)
    if f is None:
        return None
    return int(f)


def _parse_buying_factors(raw: str) -> list[dict]:
    """
    Parse multi-line buying_factors blob.

    Format: "- Factor Name (N): 'quote'"
    Returns: [{factor, count, quote}]
    Filters: only factors with count >= 1
    """
    results = []
    if not raw:
        return results
    for line in raw.split("\n"):
        line = line.strip().lstrip("- ").strip()
        if not line:
            continue
        # Match "Factor Name (N): optional quote"
        m = re.match(r"^(.+?)\s*\((\d+)\):\s*(.*)", line)
        if m:
            results.append({
                "factor": m.group(1).strip(),
                "count":  int(m.group(2)),
                "quote":  m.group(3).strip().strip('"').strip("'"),
            })
    return results


def _aggregate_themes(themes: list[dict]) -> list[dict]:
    """
    Aggregate buying factor themes across ASINs.
    Merges same factor names, sums counts, keeps highest-count quote.
    Returns sorted by count DESC.
    """
    merged: dict[str, dict] = {}
    for t in themes:
        key = t["factor"].lower()
        if key not in merged:
            merged[key] = {"factor": t["factor"], "count": t["count"], "quote": t["quote"]}
        else:
            merged[key]["count"] += t["count"]
            # Keep quote from highest count entry
            if t["count"] > merged[key]["count"] - t["count"]:
                merged[key]["quote"] = t["quote"]
    return sorted(merged.values(), key=lambda x: x["count"], reverse=True)


def _parse_eeat_blocks(raw: str) -> list[dict]:
    """
    Parse EEAT story blocks.

    Format: "[Label]: 'quote' (Context: context)"
    Returns: [{label, quote, context}]
    """
    results = []
    if not raw:
        return results
    # Split on double newlines
    blocks = re.split(r"\n\n+", raw.strip())
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        # Try to extract [Label]: quote (Context: ...)
        m = re.match(r"\[([^\]]+)\]:\s*(.*)", block, re.DOTALL)
        if m:
            label = m.group(1).strip()
            rest = m.group(2).strip()
            # Extract context if present
            ctx_m = re.search(r"\(Context:\s*([^)]+)\)", rest)
            context = ctx_m.group(1).strip() if ctx_m else ""
            quote = re.sub(r"\s*\(Context:[^)]*\)", "", rest).strip().strip('"')
            results.append({"label": label, "quote": quote, "context": context})
        else:
            # Fallback — keep as raw block
            results.append({"label": "Note", "quote": block, "context": ""})
    return results


def _parse_catalog_md_stats(md_text: str) -> dict:
    """
    Extract aggregate stats from catalog MD using regex.

    All fields are best-effort — missing fields return None.
    """
    stats: dict[str, object] = {}

    def _extract(pattern: str, text: str, group: int = 1) -> str | None:
        m = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        return m.group(group).strip() if m else None

    def _num(s: str | None) -> float | None:
        if s is None:
            return None
        try:
            return float(s.replace(",", "").replace("$", ""))
        except ValueError:
            return None

    stats["total_brands"]       = _num(_extract(r"\*\*Total brands:\*\*\s*([\d,]+)", md_text))
    stats["total_products"]     = _num(_extract(r"\*\*Total products:\*\*\s*([\d,]+)", md_text))
    stats["hhi_score"]          = _num(_extract(r"\*\*HHI Score:\*\*\s*([\d,]+)", md_text))
    stats["hhi_classification"] = _extract(r"\*\*Classification:\*\*\s*(.+)", md_text)
    stats["avg_price"]          = _num(_extract(r"\*\*Avg price:\*\*\s*\$([\d,.]+)", md_text))
    stats["median_price"]       = _num(_extract(r"\*\*Median price:\*\*\s*\$([\d,.]+)", md_text))

    # Price range: "$3.69 — $129.99"
    pr = re.search(
        r"\*\*Price range:\*\*\s*\$([\d,.]+)\s*[—–-]+\s*\$([\d,.]+)", md_text
    )
    if pr:
        stats["price_min"] = _num(pr.group(1))
        stats["price_max"] = _num(pr.group(2))

    stats["avg_asin_revenue"]   = _num(_extract(r"\*\*Avg ASIN Revenue:\*\*\s*([\d,.]+)", md_text))
    stats["avg_bsr"]            = _num(_extract(r"\*\*avg_bsr\*\*[^:]*:\s*([\d,.]+)", md_text))
    stats["avg_rating"]         = _num(_extract(r"\*\*avg_rating\*\*[^:]*:\s*([\d.]+)", md_text))
    stats["avg_review_count"]   = _num(_extract(r"\*\*avg_review_count\*\*[^:]*:\s*([\d,.]+)", md_text))

    return stats
