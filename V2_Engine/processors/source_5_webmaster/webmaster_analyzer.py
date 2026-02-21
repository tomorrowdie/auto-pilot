"""
Source 5 Webmaster — LLM Analyzer

Thin wrapper that:
1. Fills the appropriate prompt from webmaster_prompts.py
2. Calls the LLM via build_llm() (the V5 registry)
3. Returns structured or raw text output

Public API:
    generate_gsc_report(processed, provider, api_key, model, site_url) -> str
    generate_content_suggestions(processed, provider, api_key, model, site_url) -> list[dict]
    generate_bing_report(strategy_data, provider, api_key, model, site_url) -> str

JSON Repair: generate_content_suggestions uses the 6-stage repair pipeline
(same proven pattern as Source 3 rufus_analyzer.py).
"""

from __future__ import annotations

import ast
import json
import logging
import re

from V2_Engine.processors.source_5_webmaster.webmaster_prompts import fill_prompt
from V2_Engine.saas_core.auth.registry import build_llm

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# JSON Repair (6-stage — mirrors Source 3 pattern)
# ---------------------------------------------------------------------------

def _repair_json(raw: str) -> list | dict | None:
    """
    6-stage JSON repair pipeline.

    Stage 1: Strip markdown fences (```json ... ```)
    Stage 2: Remove trailing commas before ] or }
    Stage 3: Standard json.loads
    Stage 4: Brute-force wrap { ... }
    Stage 5: ast.literal_eval after true/false/null substitution
    Stage 6: Return None (caller uses skeleton fallback)
    """
    # Stage 1 — Markdown stripping
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip(), flags=re.MULTILINE)
    cleaned = cleaned.strip()

    # Stage 2 — Trailing comma cleanup
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)

    # Stage 3 — Standard parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Stage 4 — Brute-force wrap
    try:
        return json.loads("{" + cleaned + "}")
    except json.JSONDecodeError:
        pass

    # Stage 5 — Python-native pivot
    py_str = (
        cleaned
        .replace("true", "True")
        .replace("false", "False")
        .replace("null", "None")
    )
    try:
        return ast.literal_eval(py_str)
    except (ValueError, SyntaxError):
        pass

    # Stage 6 — Fail
    return None


# ---------------------------------------------------------------------------
# LLM invocation helper
# ---------------------------------------------------------------------------

def _call_llm(provider: str, api_key: str, model: str, prompt: str) -> str:
    """Build LLM and invoke with a single human message. Returns text string."""
    try:
        from langchain_core.messages import HumanMessage
    except ImportError:
        raise ImportError("pip install langchain-core")

    llm = build_llm(provider=provider, api_key=api_key, model=model, temperature=0.7)
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content if hasattr(response, "content") else str(response)


# ---------------------------------------------------------------------------
# Public: GSC — Full SEO Report (normal traffic mode)
# ---------------------------------------------------------------------------

def generate_gsc_report(
    processed: dict,
    provider: str,
    api_key: str,
    model: str,
    site_url: str,
) -> str:
    """
    Generate a 5-section Markdown SEO report from GSC processed data.

    Args:
        processed:  Output of gsc_processor.process_gsc_rows()
        provider:   Registry provider key (e.g. 'google', 'alibaba')
        api_key:    User's API key
        model:      Model ID string
        site_url:   Website URL for context (e.g. 'anergy.academy')

    Returns:
        Markdown string — the full SEO report.
    """
    summary = processed.get("summary", {})

    prompt = fill_prompt(
        "gsc_seo_report",
        SITE_URL=site_url,
        RANGE_A_START=summary.get("range_a", {}).get("startDate", "N/A"),
        RANGE_A_END=summary.get("range_a", {}).get("endDate", "N/A"),
        RANGE_B_START=summary.get("range_b", {}).get("startDate", "N/A"),
        RANGE_B_END=summary.get("range_b", {}).get("endDate", "N/A"),
        TOTAL_IMPR_A=str(summary.get("total_impr_a", 0)),
        TOTAL_IMPR_B=str(summary.get("total_impr_b", 0)),
        TOTAL_CLICKS_A=str(summary.get("total_clicks_a", 0)),
        TOTAL_CLICKS_B=str(summary.get("total_clicks_b", 0)),
        NEW_KW_COUNT=str(summary.get("new_keyword_count", 0)),
        LOST_KW_COUNT=str(summary.get("lost_keyword_count", 0)),
        RISING_KW_COUNT=str(summary.get("rising_keyword_count", 0)),
        DECLINING_KW_COUNT=str(summary.get("declining_keyword_count", 0)),
        PAGE_TWO_COUNT=str(summary.get("page_two_opportunities_count", 0)),
        NEW_KW_JSON=json.dumps(processed.get("new_keywords", []), indent=2),
        LOST_KW_JSON=json.dumps(processed.get("lost_keywords", []), indent=2),
        RISING_KW_JSON=json.dumps(processed.get("rising_keywords", []), indent=2),
        DECLINING_KW_JSON=json.dumps(processed.get("declining_keywords", []), indent=2),
        PAGE_TWO_JSON=json.dumps(processed.get("page_two_opportunities", []), indent=2),
    )

    try:
        return _call_llm(provider, api_key, model, prompt)
    except Exception as exc:
        logger.error(f"generate_gsc_report failed: {exc}")
        return f"[ERROR] GSC report generation failed: {exc}"


# ---------------------------------------------------------------------------
# Public: GSC — Content Suggestions (low traffic fallback)
# ---------------------------------------------------------------------------

def generate_content_suggestions(
    processed: dict,
    provider: str,
    api_key: str,
    model: str,
    site_url: str,
) -> list[dict]:
    """
    Generate 5 blog topic suggestions when traffic is too low for full analysis.

    Returns:
        List of dicts: [{target_keyword, blog_title, intent}, ...]
        Falls back to skeleton list if JSON repair fails.
    """
    new_kw_list = ", ".join(
        kw.get("query", "") for kw in processed.get("new_keywords", [])
    ) or "No significant keywords yet"

    prompt = fill_prompt(
        "gsc_content_ideas",
        SITE_URL=site_url,
        NEW_KW_LIST=new_kw_list,
    )

    try:
        raw = _call_llm(provider, api_key, model, prompt)
    except Exception as exc:
        logger.error(f"generate_content_suggestions LLM call failed: {exc}")
        return _content_skeleton(site_url)

    parsed = _repair_json(raw)

    if isinstance(parsed, list) and len(parsed) > 0:
        # Normalize each item
        result = []
        for item in parsed:
            if isinstance(item, dict):
                result.append({
                    "target_keyword": item.get("target_keyword", ""),
                    "blog_title":     item.get("blog_title", ""),
                    "intent":         item.get("intent", ""),
                })
        if result:
            return result

    logger.warning("generate_content_suggestions: JSON repair failed, using skeleton")
    return _content_skeleton(site_url)


def _content_skeleton(site_url: str) -> list[dict]:
    """Fallback skeleton when LLM JSON is unparseable."""
    return [
        {
            "target_keyword": "AI for Amazon sellers",
            "blog_title": f"How AI Is Changing Amazon Selling for {site_url}",
            "intent": "Awareness",
        }
    ]


# ---------------------------------------------------------------------------
# Public: Bing — GEO Strategy Report
# ---------------------------------------------------------------------------

def generate_bing_report(
    strategy_data: dict,
    provider: str,
    api_key: str,
    model: str,
    site_url: str,
) -> str:
    """
    Generate a Bing Early Signals Report from categorized strategy data.

    Args:
        strategy_data:  Output of bing_processor.categorize_bing_strategy()
        provider:       Registry provider key
        api_key:        User's API key
        model:          Model ID string
        site_url:       Website URL for context

    Returns:
        Markdown string — the Bing GEO report.
    """
    prompt = fill_prompt(
        "bing_geo_report",
        SITE_URL=site_url,
        BING_DATA_JSON=json.dumps(strategy_data, indent=2, default=str),
    )

    try:
        return _call_llm(provider, api_key, model, prompt)
    except Exception as exc:
        logger.error(f"generate_bing_report failed: {exc}")
        return f"[ERROR] Bing report generation failed: {exc}"
