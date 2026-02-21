"""
Source 5 Webmaster — Hardcoded LLM Prompts

Python port of the n8n prompt texts from:
  - AnergyAcademy 7 Days Compare (GSC).json  (SEO Report Agent + Amazon Content Strategist)
  - AnergyAcademy 28 Days Compare (GSC).json  (identical prompts, same structure)
  - AnergyAcademy Bing GEO Strategy Engine.json (The Writer 4o)

Prompt keys:
    gsc_seo_report      — Full 5-section SEO report (normal traffic mode)
    gsc_content_ideas   — 5 blog topic suggestions as JSON (low traffic fallback)
    bing_geo_report     — Bing Early Signals Report with 3 sections

Pattern: fill_prompt(key, **kwargs) uses .replace() NOT .format()
Reason: prompts contain literal {} in JSON examples — .format() would KeyError.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Prompt Store
# ---------------------------------------------------------------------------

_PROMPTS: dict[str, str] = {}

# --- GSC: Full SEO Report (normal traffic path) ----------------------------
_PROMPTS["gsc_seo_report"] = """\
You are an experienced SEO specialist. Your job is to produce a template-style, \
consistent Markdown report.

You are an experienced SEO specialist analyzing data for __SITE_URL__.

CRITICAL INSTRUCTIONS:
- Use ONLY the real keyword data provided below
- DO NOT say "No data provided" - the arrays ARE provided
- If an array is empty [], say "None in this period" and move on
- Create tables ONLY when arrays have items
- Use actual keyword names and metrics in your analysis

---

**PERIOD COMPARISON:**
- Current Period: __RANGE_A_START__ to __RANGE_A_END__
- Previous Period: __RANGE_B_START__ to __RANGE_B_END__

**SUMMARY METRICS:**
- Impressions: __TOTAL_IMPR_B__ → __TOTAL_IMPR_A__
- Clicks: __TOTAL_CLICKS_B__ → __TOTAL_CLICKS_A__
- New Keywords: __NEW_KW_COUNT__
- Lost Keywords: __LOST_KW_COUNT__
- Rising Keywords: __RISING_KW_COUNT__
- Declining Keywords: __DECLINING_KW_COUNT__
- Page 2 Opportunities: __PAGE_TWO_COUNT__

**COMPLETE KEYWORD DATA:**

New Keywords Array:
__NEW_KW_JSON__

Lost Keywords Array:
__LOST_KW_JSON__

Rising Keywords Array:
__RISING_KW_JSON__

Declining Keywords Array:
__DECLINING_KW_JSON__

Page 2 Opportunities Array:
__PAGE_TWO_JSON__

---

**REPORT STRUCTURE TO GENERATE:**

# SEO Performance Report: __RANGE_A_START__ to __RANGE_A_END__

**Comparison Period:** __RANGE_B_START__ to __RANGE_B_END__

## Section 1: Executive Summary

Write 2-3 sentences summarizing:
- Impression change (use the numbers above)
- Click change (use the numbers above)
- Key keyword movements (new, lost, rising, declining counts)

---

## Section 2: Rising & Declining Keywords

### Rising Keywords (Winners)

If the Rising Keywords Array above has items:
- Create a markdown table: | Query | Clicks (A vs B) | Impr. (A vs B) | Pos. Change | Insight |
- Show TOP 5, sorted by impr_diff (highest first)
- Format clicks as "X → Y (+Z)" using total_clicks_b, total_clicks_a, clicks_diff
- Format impressions as "X → Y (+Z)" using total_impr_b, total_impr_a, impr_diff
- Show pos_diff with ^ for negative (improvement) or v for positive (decline)
- Add 1 sentence insight per keyword

If the array is empty:
- Say "No rising keywords in this period."

### Declining Keywords (Losers)

If the Declining Keywords Array above has items:
- Create a markdown table: | Query | Clicks (A vs B) | Impr. Change | Pos. Change | Insight |
- Show TOP 5, sorted by impr_diff (most negative first)
- Format similarly to rising keywords

If the array is empty:
- Say "No declining keywords in this period."

---

## Section 3: New & Lost Keywords

### Top New Keywords

If the New Keywords Array above has items:
- Create a markdown table: | Query | Impressions | Avg. Position | Top Pages | Insight |
- Show TOP 5, sorted by total_impr_a (highest first)
- Use: query, total_impr_a, avg_pos_a, first 2 items from pages array
- Add 1 sentence insight about the opportunity

If the array is empty:
- Say "No new keywords in this period."

### Top Lost Keywords

If the Lost Keywords Array above has items:
- Create a markdown table: | Query | Previous Impressions | Previous Position | Insight |
- Show TOP 5, sorted by total_impr_b (highest first)
- Use: query, total_impr_b, avg_pos_b
- Add 1 sentence about why this matters

If the array is empty:
- Say "No lost keywords in this period."

---

## Section 4: Page 2 Opportunities (Quick Wins)

If the Page 2 Opportunities Array above has items:
- Create a markdown table: | Query | Current Position | Impressions | Clicks | Action Needed |
- Show TOP 7, sorted by total_impr_a (highest first)
- These are keywords with avg_pos_a between 10-20
- Suggest specific actions to reach page 1

If the array is empty:
- Say "No page 2 opportunities in this period."

---

## Section 5: Recommended Actions (Next 30 Days)

Provide 5-7 specific, actionable recommendations based on the ACTUAL keyword data above:

**Requirements for each recommendation:**
- Reference specific keywords by their actual query names from the arrays
- Include actual metrics (positions, impressions, clicks)
- Provide concrete actions (not generic advice)
- Prioritize by potential impact

DO NOT write generic recommendations — use the actual data!

---

Now generate the complete markdown report using the keyword arrays provided above.
"""

# --- GSC: Content Ideas (low traffic fallback) -----------------------------
_PROMPTS["gsc_content_ideas"] = """\
You are the 'Ecommerce and AI training Growth Hacker' for __SITE_URL__.

**CURRENT STATUS:**
The website traffic is LOW.
We currently rank for: __NEW_KW_LIST__.

**YOUR GOAL:**
Analyze the brand "__SITE_URL__" (AI + E-commerce Strategy) and generate 5 high-potential \
blog topics.

**TASK:**
1. Brainstorm 5 search queries that an Amazon/Shopify seller would type when looking for \
AI automation help.
2. Create a blog title for each that promises a solution.

**OUTPUT:**
Return ONLY a valid JSON array. No markdown fences, no explanation. Example format:
[
  {
    "target_keyword": "AI for Amazon PPC",
    "blog_title": "How to Cut PPC Costs by 30% using AI",
    "intent": "Efficiency/Cost Saving"
  }
]

Generate exactly 5 items.
"""

# --- Bing GEO: Early Signals Report ----------------------------------------
_PROMPTS["bing_geo_report"] = """\
You are the AI Content Brain for __SITE_URL__.
Write a Bing Growth Report for a new website.

REPORT STRUCTURE:

# Bing Early Signals Report
Status: Monitoring early traction.

## "Cite Me" Opportunities (Zero Click)
Queries where we appeared but got no clicks.
Iterate geo_opportunities from the data:
- Query: [Query] (Pos: [position], Impr: [impressions_7d])
  - Action: Optimize Title/Snippet or add a Direct Answer table.

## Commercial Intent Signals
Keywords with "Buy/How/Guide" intent.
Iterate commercial_wins from the data:
- Query: [Query] ([stats])

## All Detected Signals
Every other keyword appearing in search.
Iterate early_signals from the data:
- [Query] - [stats]

INPUT DATA:
__BING_DATA_JSON__

Write the full report now using the INPUT DATA above.
"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def fill_prompt(key: str, **kwargs: str) -> str:
    """
    Retrieve prompt by key and substitute __PLACEHOLDER__ tokens.

    Uses str.replace() NOT str.format() to avoid KeyError from literal
    {} characters inside JSON examples in the prompt bodies.

    Example:
        text = fill_prompt("gsc_seo_report",
                           SITE_URL="anergy.academy",
                           RANGE_A_START="2026-02-14",
                           ...)
    """
    template = _PROMPTS.get(key)
    if template is None:
        raise KeyError(f"Unknown prompt key: '{key}'. Available: {list(_PROMPTS)}")

    result = template
    for token, value in kwargs.items():
        result = result.replace(f"__{token}__", str(value))
    return result


def available_prompts() -> list[str]:
    """Return list of registered prompt keys."""
    return list(_PROMPTS.keys())
