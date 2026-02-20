"""
Source 2 — Review Analyzer (LLM-powered Happy/Defect analysis).

Sends batches of reviews to a Google Gemini endpoint and parses
structured JSON responses for Brand DNA (happy) or Defect Tracker (defect).

Uses the EXACT prompts from the n8n reference workflow (see prompts.py).

Usage:
    from V2_Engine.processors.source_2_reviews.reviews_analyzer import (
        analyze_reviews,
    )
    results = analyze_reviews(df, api_config)
"""

from __future__ import annotations

import json
import re
import time

import pandas as pd
from langchain_core.messages import HumanMessage, SystemMessage

from V2_Engine.saas_core.auth.registry import build_llm
from V2_Engine.processors.source_2_reviews.prompts import (
    HAPPY_SYSTEM_PROMPT,
    HAPPY_USER_PROMPT,
    DEFECT_SYSTEM_PROMPT,
    DEFECT_USER_PROMPT,
    HAPPY_THRESHOLD,
    DEFECT_THRESHOLD,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_MAX_REVIEWS_PER_BATCH = 50


# ---------------------------------------------------------------------------
# Step A: Prepare review batch for LLM context
# ---------------------------------------------------------------------------
def _prepare_batch(df: pd.DataFrame) -> list[dict]:
    """
    Convert a DataFrame into a lightweight list of dicts for the LLM prompt.

    Keeps only the fields relevant to analysis. Limits to top 50 reviews
    by helpful_votes (then by review_length) to fit in context window.
    """
    if df.empty:
        return []

    # Sort: most helpful first, then longest reviews
    df_sorted = df.sort_values(
        by=["helpful_votes", "review_length"],
        ascending=[False, False],
    ).head(_MAX_REVIEWS_PER_BATCH)

    records = []
    for _, row in df_sorted.iterrows():
        records.append({
            "title": str(row.get("review_title", "")),
            "content": str(row.get("review_content", "")),
            "rating": float(row.get("rating", 0)),
            "date": str(row.get("review_date", ""))[:10],
            "variant": str(row.get("variant", "")),
            "helpful_votes": int(row.get("helpful_votes", 0)),
            "is_verified": bool(row.get("is_verified_purchase", False)),
        })

    return records


# ---------------------------------------------------------------------------
# Step C: LLM call via V5 registry (LangChain)
# ---------------------------------------------------------------------------
def _call_llm(
    system_prompt: str,
    user_prompt: str,
    provider: str,
    api_key: str,
    model: str,
) -> str:
    """
    Call any supported LLM provider via the V5 registry.

    Args:
        system_prompt: The system instruction text.
        user_prompt:   The user message (contains review data).
        provider:      Registry key (e.g. 'google', 'openai', 'anthropic').
        api_key:       Provider API key.
        model:         Model name.

    Returns:
        Raw text response from the model.

    Raises:
        RuntimeError on API failure.
    """
    llm = build_llm(provider, api_key, model, temperature=0.2)
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]
    response = llm.invoke(messages)
    return response.content


# ---------------------------------------------------------------------------
# Step D: Parse LLM response JSON
# ---------------------------------------------------------------------------
def _parse_llm_json(raw_text: str) -> dict:
    """
    Parse the LLM response into a Python dict.

    Strips markdown code fences if present, then json.loads().
    """
    cleaned = raw_text.strip()

    # Strip ```json ... ``` fences
    cleaned = re.sub(r"^```json\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"```\s*$", "", cleaned)
    cleaned = cleaned.strip()

    return json.loads(cleaned)


# ---------------------------------------------------------------------------
# Step B+C+D: Analyze a single batch (one ASIN, one sentiment)
# ---------------------------------------------------------------------------
def analyze_batch(
    df: pd.DataFrame,
    api_key: str,
    model: str = "gemini-2.5-flash",
    flow: str = "happy",
    provider: str = "google",
) -> dict | None:
    """
    Analyze a batch of reviews for a single flow (happy or defect).

    Args:
        df:       DataFrame of reviews (already filtered to one ASIN + sentiment).
        api_key:  Provider API key.
        model:    Model name.
        flow:     "happy" or "defect".
        provider: Registry key (e.g. 'google', 'openai', 'anthropic').

    Returns:
        Parsed JSON dict (Brand DNA or Defect Report), or None if empty.
    """
    if df.empty:
        return None

    # Step A: Prepare
    reviews = _prepare_batch(df)
    if not reviews:
        return None

    reviews_json = json.dumps(reviews, ensure_ascii=False)

    # Step B: Select prompts
    if flow == "happy":
        system_prompt = HAPPY_SYSTEM_PROMPT
        user_prompt = HAPPY_USER_PROMPT.format(reviews_json=reviews_json)
    elif flow == "defect":
        system_prompt = DEFECT_SYSTEM_PROMPT
        user_prompt = DEFECT_USER_PROMPT.format(reviews_json=reviews_json)
    else:
        raise ValueError(f"Unknown flow: {flow}. Use 'happy' or 'defect'.")

    # Step C: Call LLM
    print(f"[Review Analyzer] Sending {len(reviews)} reviews to {provider}/{model} ({flow} flow)...")
    raw_response = _call_llm(system_prompt, user_prompt, provider, api_key, model)

    # Step D: Parse
    result = _parse_llm_json(raw_response)
    print(f"[Review Analyzer] Parsed {flow} result for: {result.get('product_name', 'unknown')}")

    return result


# ---------------------------------------------------------------------------
# High-level orchestrator: analyze all ASINs in a DataFrame
# ---------------------------------------------------------------------------
def analyze_reviews(
    df: pd.DataFrame,
    api_config: dict,
) -> dict:
    """
    Full analysis pipeline: split by ASIN + sentiment, batch to LLM.

    Args:
        df:         Full review DataFrame (from ingestor).
        api_config: Dict from V5 auth_manager, containing:
                    {"key": "...", "model": "gemini-2.5-flash", "provider": "google"}

    Returns:
        {
            "happy_results":  [dict, ...],   # One Brand DNA per ASIN
            "defect_results": [dict, ...],   # One Defect Report per ASIN
            "stats": {
                "total_reviews": int,
                "happy_count": int,
                "defect_count": int,
                "asins_processed": int,
            },
        }
    """
    api_key = api_config["key"]
    model = api_config.get("model", "gemini-2.5-flash")
    provider = api_config.get("provider", "google")

    # Split by sentiment
    happy_df = df[df["rating"] >= HAPPY_THRESHOLD]
    defect_df = df[df["rating"] <= DEFECT_THRESHOLD]

    happy_results = []
    defect_results = []
    asins_processed = set()

    # --- Happy Flow: group by ASIN ---
    if not happy_df.empty:
        for asin, asin_df in happy_df.groupby("asin"):
            print(f"[Review Analyzer] Happy flow — ASIN: {asin} ({len(asin_df)} reviews)")
            try:
                result = analyze_batch(asin_df, api_key, model, flow="happy", provider=provider)
                if result:
                    result["_asin"] = asin
                    result["_review_count"] = len(asin_df)
                    happy_results.append(result)
                    asins_processed.add(asin)
            except Exception as e:
                print(f"[Review Analyzer] ERROR (happy, {asin}): {e}")
                happy_results.append({
                    "_asin": asin,
                    "_review_count": len(asin_df),
                    "_error": str(e),
                })

            # Rate limit pause between ASINs
            time.sleep(1)

    # --- Defect Flow: group by ASIN ---
    if not defect_df.empty:
        for asin, asin_df in defect_df.groupby("asin"):
            print(f"[Review Analyzer] Defect flow — ASIN: {asin} ({len(asin_df)} reviews)")
            try:
                result = analyze_batch(asin_df, api_key, model, flow="defect", provider=provider)
                if result:
                    result["_asin"] = asin
                    result["_review_count"] = len(asin_df)
                    defect_results.append(result)
                    asins_processed.add(asin)
            except Exception as e:
                print(f"[Review Analyzer] ERROR (defect, {asin}): {e}")
                defect_results.append({
                    "_asin": asin,
                    "_review_count": len(asin_df),
                    "_error": str(e),
                })

            time.sleep(1)

    return {
        "happy_results": happy_results,
        "defect_results": defect_results,
        "stats": {
            "total_reviews": len(df),
            "happy_count": len(happy_df),
            "defect_count": len(defect_df),
            "asins_processed": len(asins_processed),
        },
    }


# ---------------------------------------------------------------------------
# Flatten helpers (for Parquet/DataFrame output)
# ---------------------------------------------------------------------------
def flatten_happy_results(results: list[dict]) -> pd.DataFrame:
    """
    Flatten Brand DNA results into a DataFrame (one row per ASIN).

    Matches the n8n "Markdown Converter - happy" logic.
    """
    rows = []
    for item in results:
        if "_error" in item:
            rows.append({
                "asin": item.get("_asin", ""),
                "product_name": "",
                "primary_hook": f"ERROR: {item['_error']}",
                "buying_factors": "",
                "cosmo_intents": "",
                "rufus_keywords": "",
                "eeat_stories": "",
                "competitor_wins": "",
            })
            continue

        dna = item.get("brand_dna", {})

        # Join lists into readable strings (matches n8n converter)
        intents = dna.get("cosmo_intents", [])
        intents_text = "\n".join(f"- {i}" for i in intents) if intents else ""

        keywords = dna.get("rufus_keywords", [])
        keywords_text = ", ".join(keywords) if keywords else ""

        wins = dna.get("competitor_wins", [])
        wins_text = "\n".join(f"- {w}" for w in wins) if wins else ""

        experiences = dna.get("eeat_experiences", [])
        eeat_text = "\n\n".join(
            f'[{e.get("angle", "")}]: "{e.get("quote", "")}" '
            f'(Context: {e.get("context", "")})'
            for e in experiences
        ) if experiences else ""

        # Buying Factors (new — for chart + KB)
        factors = dna.get("buying_factors", [])
        factors_text = "\n".join(
            f"- {f.get('factor', '')} ({f.get('count', 0)}): \"{f.get('quote', '')}\""
            for f in factors
        ) if factors else ""

        rows.append({
            "asin": item.get("_asin", ""),
            "product_name": item.get("product_name", ""),
            "primary_hook": dna.get("primary_hook", ""),
            "buying_factors": factors_text,
            "cosmo_intents": intents_text,
            "rufus_keywords": keywords_text,
            "eeat_stories": eeat_text,
            "competitor_wins": wins_text,
        })

    return pd.DataFrame(rows) if rows else pd.DataFrame()


def flatten_buying_factors(results: list[dict]) -> pd.DataFrame:
    """
    Flatten buying_factors into a DataFrame (one row per factor per ASIN).

    Used for bar chart visualization in the Happy DNA tab.
    """
    rows = []
    for item in results:
        if "_error" in item:
            continue
        dna = item.get("brand_dna", {})
        for f in dna.get("buying_factors", []):
            rows.append({
                "asin": item.get("_asin", ""),
                "product_name": item.get("product_name", ""),
                "factor": f.get("factor", ""),
                "count": f.get("count", 0),
                "quote": f.get("quote", ""),
            })
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def flatten_defect_results(results: list[dict]) -> pd.DataFrame:
    """
    Flatten Defect Tracker results into a DataFrame (one row per issue).

    Matches the n8n "Markdown Converter - defects" logic.
    """
    rows = []
    for item in results:
        if "_error" in item:
            rows.append({
                "asin": item.get("_asin", ""),
                "product_name": "",
                "category": "",
                "total_reviews": item.get("_review_count", 0),
                "primary_complaint": f"ERROR: {item['_error']}",
                "issue": "",
                "count": 0,
                "representative_quote": "",
                "impacted_traffic_layer": "",
                "risked_system_tag": "",
                "issue_share": 0.0,
            })
            continue

        summary = item.get("batch_summary", {})
        total = summary.get("total_reviews", 1) or 1  # avoid div-by-zero
        issues = summary.get("impact_analysis", [])

        for issue in issues:
            count = issue.get("count", 0)
            rows.append({
                "asin": item.get("_asin", ""),
                "product_name": item.get("product_name", ""),
                "category": item.get("category", ""),
                "total_reviews": total,
                "primary_complaint": summary.get("primary_complaint", ""),
                "issue": issue.get("issue", ""),
                "count": count,
                "representative_quote": issue.get("representative_quote", ""),
                "impacted_traffic_layer": issue.get("impacted_traffic_layer", ""),
                "risked_system_tag": issue.get("risked_system_tag", ""),
                "issue_share": round(count / total, 4),
            })

    return pd.DataFrame(rows) if rows else pd.DataFrame()
