"""
Source 6 — LLM Chain for SEO Writer Engine (Epic 2)

3-stage sequential pipeline:
  Part 0 : Architecture Brief  — brand / audience / keyword context
  Part 1 : Article Outline     — section structure + H-tag plan
  Part 2 : Full Draft          — complete article, ready to publish

Each stage injects the previous stage's output invisibly as context.
Prompt templates are loaded from V2_Engine/prompts/active/seo_prompt_part{0,1,2}.md.
If the files are empty, built-in stub prompts are used automatically.

LLM caller is modular — PM will plug in Gemini / Qwen API key later.
Until then, model="mock" returns realistic demo content instantly.
"""

from __future__ import annotations

import json
import os
import re
import time

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
_PROMPT_DIR = os.path.join(_PROJECT_ROOT, "V2_Engine", "prompts", "active")


# ---------------------------------------------------------------------------
# Built-in stub prompts (used when PM prompt files are still empty)
# ---------------------------------------------------------------------------
_DEFAULT_T0 = (
    "You are an expert SEO content strategist. Produce a concise content architecture "
    "brief (300–400 words) for a high-ranking article.\n\n"
    "PRIMARY KEYWORD   : [PRIMARY_KEYWORD]\n"
    "SECONDARY KEYWORDS: [SECONDARY_KEYWORD]\n"
    "COSMO INTENT      : [INTENT]\n"
    "BRAND             : [BRAND]\n"
    "INDUSTRY / NICHE  : [INDUSTRY]\n"
    "TARGET AUDIENCE   : [TARGET_AUDIENCE]\n"
    "TONE              : [TONE]\n"
    "TARGET LENGTH     : [ARTICLE_LENGTH] words\n\n"
    "Output: angle selection, EEAT signal plan, primary H-tag structure proposal, "
    "semantic keyword clusters to weave in."
)

_DEFAULT_T1 = (
    "Based on this content brief:\n\n"
    "--- BRIEF START ---\n"
    "[PART0_OUTPUT]\n"
    "--- BRIEF END ---\n\n"
    "Create a detailed article outline for: [PRIMARY_KEYWORD]\n\n"
    "Format: numbered H2 sections, each with 2-3 H3 sub-sections and bullet-point "
    "content directions. Include a FAQ section and a Conclusion."
)

_DEFAULT_T2 = (
    "Based on this outline:\n\n"
    "--- OUTLINE START ---\n"
    "[PART1_OUTPUT]\n"
    "--- OUTLINE END ---\n\n"
    "Write the complete, publish-ready SEO article in Markdown.\n\n"
    "Requirements:\n"
    "- Title (H1) naturally contains: [PRIMARY_KEYWORD]\n"
    "- Meta Description (italic, under title, ≤ 155 chars)\n"
    "- Introduction hooks the reader and includes the primary keyword in first 100 words\n"
    "- All outlined sections fully developed\n"
    "- Secondary keywords woven naturally: [SECONDARY_KEYWORD]\n"
    "- COSMO intent satisfied: [INTENT]\n"
    "- FAQ section with 5 questions (use H3 for each)\n"
    "- Conclusion with a clear CTA\n"
    "- Tone: [TONE]\n"
    "- Target length: [ARTICLE_LENGTH] words\n\n"
    "INTERNAL LINKING RULES:\n"
    "You are equipped with the site's actual live URLs:\n"
    "[LIVE_SITEMAP_URLS]\n\n"
    "1. AUTO-MATCH: Scan the article for topics, products, and themes that correspond to any URL "
    "in the approved list above. Insert 2–5 contextually natural internal links using keyword-rich anchor text.\n"
    "2. FUTURE CLUSTERS: For Sister Cluster topics not yet live, format URLs strictly as: "
    "[WEBSITE_BASE]/blog/[kebab-case-cluster-name]\n"
    "3. STRICT RULE: Do NOT invent, guess, or hallucinate any URL. "
    "If no URL in the approved list matches a topic, omit the internal link entirely.\n\n"
    "KNOWLEDGE BASE CONTEXT (brand, market, reviews, rufus intelligence):\n"
    "[KNOWLEDGE_BASE]\n\n"
    "MANDATORY OUTPUT FORMAT — YOUR ENTIRE RESPONSE MUST BE ONLY THESE THREE BLOCKS:\n"
    "Do NOT write any content before ===TITLE===.\n"
    "Do NOT write any content after ===END_TECHNICAL_SEO===.\n"
    "Output each piece of content ONCE, inside the correct block.\n\n"
    "===TITLE===\n"
    "[H1 title — plain text, no # prefix, under 75 characters]\n"
    "===END_TITLE===\n\n"
    "===ARTICLE_BODY===\n"
    "[Full article Markdown — H1 through Conclusion. No <meta>, <title>, or <script> tags here.]\n"
    "===END_ARTICLE_BODY===\n\n"
    "===TECHNICAL_SEO===\n"
    "[All HTML meta tags, JSON-LD <script> blocks, Open Graph, Twitter Cards, Pinterest elements.]\n"
    "===END_TECHNICAL_SEO==="
)

# ---------------------------------------------------------------------------
# Mock article template (returned in mock mode)
# ---------------------------------------------------------------------------
_MOCK_ARTICLE = """\
# {primary_kw}: The Complete Guide for {audience}

*Everything you need to know about {primary_kw} — backed by real customer insights and expert recommendations.*

## Introduction

Choosing the right **{primary_kw}** can feel overwhelming. With dozens of options flooding the market, how do you know which one truly delivers?

This guide cuts through the noise. We've analysed hundreds of real customer reviews, identified the top pain points, and distilled everything into one actionable resource — so you can make a confident decision the first time.

---

## 1. What Makes a Great {primary_kw}?

### 1.1 Core Quality Signals

Not all products are created equal. The best options share three non-negotiable traits:

- **Safety-first materials** — look for BPA-free, food-grade certifications
- **Ergonomic design** — fits naturally in hand, reduces fatigue
- **Easy to clean** — dishwasher-safe or single-piece construction

### 1.2 What Customers Actually Care About

After reviewing thousands of verified purchases, the top purchase drivers are:

1. Durability over repeated use
2. Ease of cleaning (dishwasher compatibility)
3. Value for money vs premium alternatives

---

## 2. How to Choose the Right Option for Your Needs

### 2.1 Match to Your Specific Use Case

Different scenarios call for different features. Consider:

- **Everyday home use** — prioritise durability and ease of cleaning
- **On-the-go / travel** — compact, spill-proof designs win
- **Gift purchase** — presentation and packaging matter as much as function

### 2.2 Size & Fit Considerations

Sizing guidance:
- Measure your primary use case requirements before purchasing
- Check brand-specific size charts — they vary significantly
- When in doubt, size up — most returns are from sizing too small

---

## 3. Expert Tips and Common Mistakes to Avoid

### 3.1 The Top 3 Mistakes Buyers Make

1. **Ignoring cleaning requirements** — some designs look great but are a nightmare to clean
2. **Buying single units** — most use cases benefit from having 2–3 on hand
3. **Overlooking warranty terms** — premium brands back their products; budget brands rarely do

### 3.2 Pro Tips from Power Users

Customers who are most satisfied consistently mention:

- Buying a set rather than individual units
- Checking the return policy before purchasing
- Reading reviews filtered by verified purchase only

---

## Frequently Asked Questions

### Is {primary_kw} safe to use daily?

Yes — provided it meets current safety certifications. Look for BPA-free labelling and food-grade material declarations.

### How long does a quality {primary_kw} typically last?

With proper care, premium options last 2–5 years. Budget options average 6–12 months before showing wear.

### What's the best way to clean a {primary_kw}?

Most premium options are dishwasher-safe (top rack). For hand washing, warm soapy water and a soft brush is sufficient.

### Can I use it straight out of the box?

Yes — though we recommend a quick rinse with warm water before first use.

### What should I look for in the packaging?

Sealed, tamper-evident packaging is a quality signal. Avoid products with damaged seals or no certification markings.

---

## Conclusion

Finding the right **{primary_kw}** comes down to three things: matching your specific use case, prioritising quality over price, and reading real customer reviews.

Use the insights in this guide to shortlist your options — then cross-reference with the latest customer feedback to make your final call.

**Ready to choose?** Browse our top-rated picks above, or use the comparison tool to find your perfect match.
"""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_prompt(filename: str) -> str:
    """Load a prompt template file. Returns empty string if missing or empty."""
    path = os.path.join(_PROMPT_DIR, filename)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""


def _book_to_context(book: dict | None) -> str:
    """
    Convert the canonical Book dict to a compact JSON string for LLM injection.
    Caps large arrays to avoid context overflow — keeps the most signal-dense slices.
    """
    if not book:
        return "(no knowledge base data available)"
    try:
        web = book.get("webmaster_book", {})
        compact = {
            "meta":    book.get("meta", {}),
            "catalog": {
                "market_summary":  book.get("catalog_book", {}).get("market_summary", {}),
                "revenue_leaders": book.get("catalog_book", {}).get("revenue_leaders", [])[:5],
            },
            "traffic": {
                "top_keywords": book.get("traffic_book", {}).get("top_keywords", [])[:30],
                "summary":      book.get("traffic_book", {}).get("summary", {}),
            },
            "reviews": {
                "happy_themes":   book.get("reviews_book", {}).get("happy_themes", [])[:15],
                "defect_themes":  book.get("reviews_book", {}).get("defect_themes", [])[:15],
                "cosmo_intents":  book.get("reviews_book", {}).get("cosmo_intents", [])[:10],
                "eeat_proof":     book.get("reviews_book", {}).get("eeat_proof", [])[:10],
                "rufus_keywords": book.get("reviews_book", {}).get("rufus_keywords", [])[:20],
                "summary":        book.get("reviews_book", {}).get("summary", {}),
            },
            "rufus": {
                "trap_questions": book.get("rufus_book", {}).get("trap_questions", [])[:15],
                "dealbreakers":   book.get("rufus_book", {}).get("dealbreakers", []),
                "hero_scenarios": book.get("rufus_book", {}).get("hero_scenarios", []),
                "listing_gaps":   book.get("rufus_book", {}).get("listing_gaps", []),
                "seo_flags":      book.get("rufus_book", {}).get("seo_flags", []),
                "summary":        book.get("rufus_book", {}).get("summary", {}),
            },
            "webmaster": {
                "gsc_summary":      web.get("gsc", {}).get("summary", {}),
                "rising_keywords":  web.get("gsc", {}).get("rising_keywords", [])[:10],
                "page_two_opps":    web.get("gsc", {}).get("page_two_opportunities", [])[:10],
                "bing_top_queries": web.get("bing", {}).get("top_queries", [])[:10],
                "geo_signals":      web.get("geo_signals", [])[:10],
                "summary":          web.get("summary", {}),
            },
        }
        return json.dumps(compact, indent=2, ensure_ascii=False)
    except Exception as exc:
        return f"(book serialization error: {exc})"


def _extract_sitemap_urls(book: dict | None) -> str:
    """
    Extract real page URLs from webmaster data for internal link grounding.

    Sources (in priority order):
      1. webmaster_book.bing.top_pages   — most reliable; each item has a 'page' field
      2. webmaster_book.gsc.page_two_opportunities — position 8–20 pages
      3. webmaster_book.gsc.new_keywords  — may carry page context

    Returns a bullet-list string, capped at 100 URLs.
    Falls back to a placeholder if no webmaster data is available.
    """
    if not book:
        return "(no sitemap data — connect Source 5 Webmaster to enable live URLs)"

    web = book.get("webmaster_book", {})
    if web.get("status") == "no_data":
        return "(no sitemap data — connect Source 5 Webmaster to enable live URLs)"

    seen: set[str] = set()
    urls: list[str] = []

    def _add(item: dict) -> None:
        url = (
            item.get("page") or item.get("url") or
            item.get("landing_page") or item.get("keys", [""])[0]
            if isinstance(item, dict) else ""
        )
        if url and url.startswith("http") and url not in seen:
            seen.add(url)
            urls.append(url)

    # 1. Bing top pages (best source)
    for item in web.get("bing", {}).get("top_pages", []):
        _add(item)

    # 2. GSC page-two opportunities
    for item in web.get("gsc", {}).get("page_two_opportunities", []):
        _add(item)

    # 3. GSC new keywords (may carry page context)
    for item in web.get("gsc", {}).get("new_keywords", []):
        _add(item)

    urls = urls[:100]

    if not urls:
        return "(no page URLs found in webmaster data — run Source 5 analysis first)"

    return "\n".join(f"- {u}" for u in urls)


def _base_vars(inputs: dict, book: dict | None = None) -> dict:
    """Build the full variable dict from inputs — maps to [KEY] placeholders in prompt files."""
    secondary_kws = inputs.get("secondary_kws", [])
    secondary_str = (
        ", ".join(secondary_kws)
        if isinstance(secondary_kws, list)
        else str(secondary_kws)
    )
    return {
        # Keyword targeting
        "primary_kw":        inputs.get("primary_kw", ""),
        "primary_keyword":   inputs.get("primary_kw", inputs.get("primary_keyword", "")),
        "secondary_kws":     secondary_str,
        "secondary_keyword": inputs.get("secondary_keyword", secondary_str),
        "intent":            inputs.get("intent", ""),
        # Writing style
        "tone":              inputs.get("tone", "Informative"),
        "article_length":    str(inputs.get("article_length", 1500)),
        # Brand identity
        "brand":             inputs.get("brand", ""),
        "industry":          inputs.get("industry", ""),
        "founded":           inputs.get("founded", ""),
        "core_values":       inputs.get("core_values", ""),
        "brand_heritage":    inputs.get("brand_heritage", ""),
        "mission":           inputs.get("mission", ""),
        "brand_story":       inputs.get("brand_story", ""),
        "distribution":      inputs.get("distribution", ""),
        "target_audience":   inputs.get("target_audience", inputs.get("audience", "customers")),
        "audience":          inputs.get("audience", inputs.get("target_audience", "customers")),
        "website_base":      inputs.get("website_base", ""),
        # Content project
        "main_topic":        inputs.get("main_topic", inputs.get("primary_kw", "")),
        "target_location":   inputs.get("target_location", ""),
        "content_level":     inputs.get("content_level", "CLUSTER_L3"),
        # Site architecture
        "main_pillar_page":  inputs.get("main_pillar_page", ""),
        "sub_pillar_page":   inputs.get("sub_pillar_page", ""),
        "sister_clusters":   inputs.get("sister_clusters", ""),
        # Knowledge base — injected from the Book JSON (Source 0–5 intelligence)
        "knowledge_base":    _book_to_context(book),
        "live_sitemap_urls": _extract_sitemap_urls(book),
    }


def _hydrate(template: str, variables: dict) -> str:
    """Safe token replacement using [KEY] syntax — case-insensitive, avoids .format() KeyErrors."""
    result = template
    for key, val in variables.items():
        pattern = re.escape(f"[{key}]")
        result = re.sub(pattern, lambda m, r=str(val): r, result, flags=re.IGNORECASE)
    return result


def _clean_for_display(md_text: str) -> str:
    """
    Strip backend SEO scaffolding from Markdown before rendering in Streamlit.

    Removes:
    - <script>...</script> blocks (single- and multi-line)
    - Standalone <meta ...> tags
    - Standalone <title>...</title> tags
    - Fenced code blocks that contain only HTML tags (```html ... ```)
    """
    cleaned = md_text

    # 1. Remove <script> blocks (multiline)
    cleaned = re.sub(r"<script\b[^>]*>.*?</script>", "", cleaned, flags=re.DOTALL | re.IGNORECASE)

    # 2. Remove <meta ...> self-closing tags (whole line)
    cleaned = re.sub(r"^\s*<meta\b[^>]*/?\s*>\s*$", "", cleaned, flags=re.MULTILINE | re.IGNORECASE)

    # 3. Remove <title>...</title> tags (single line)
    cleaned = re.sub(r"^\s*<title\b[^>]*>.*?</title>\s*$", "", cleaned, flags=re.MULTILINE | re.IGNORECASE)

    # 4. Remove fenced ```html blocks that are pure tag scaffolding (no prose)
    def _strip_html_fence(m: re.Match) -> str:
        body = m.group(1)
        # If the block contains only HTML tags (no plain prose words), drop it
        prose = re.sub(r"<[^>]+>", "", body).strip()
        return "" if not prose else m.group(0)

    cleaned = re.sub(r"```html\n(.*?)```", _strip_html_fence, cleaned, flags=re.DOTALL)

    # 5. Collapse runs of blank lines left by the removals
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    return cleaned.strip()


def parse_structured_output(raw: str) -> dict:
    """
    Extract the three sentinel-delimited sections from Stage 2 output.

    Expected format (enforced by the prompt):
        ===TITLE===          ... ===END_TITLE===
        ===ARTICLE_BODY===   ... ===END_ARTICLE_BODY===
        ===TECHNICAL_SEO===  ... ===END_TECHNICAL_SEO===

    Fallback: if sentinels are absent (old cached result, mock run, or
    model non-compliance), title is extracted from the first H1 line,
    body is cleaned via _clean_for_display(), and tech_seo is empty.
    """
    def _extract(marker: str) -> str:
        # No \s* inside the pattern — capture everything between sentinels, then strip
        m = re.search(rf"==={marker}===(.*?)===END_{marker}===", raw, re.DOTALL | re.IGNORECASE)
        return m.group(1).strip() if m else ""

    title    = _extract("TITLE")
    body     = _extract("ARTICLE_BODY")
    tech_seo = _extract("TECHNICAL_SEO")

    # --- Fallback: sentinels absent ---
    if not body:
        cleaned = _clean_for_display(raw)
        body = (
            "> ⚠️ **Parser Note:** The model did not use the expected sentinel format. "
            "Cleaned output is shown below. Re-generate to get structured output.\n\n"
            "---\n\n"
            + cleaned
        )

    if not title:
        h1_match = re.search(r"^#\s+(.+)$", body or raw, re.MULTILINE)
        title = h1_match.group(1).strip() if h1_match else ""

    return {"title": title, "body": body, "tech_seo": tech_seo}


# Keep underscore alias for backward compat with any cached pyc that references it
_parse_structured_output = parse_structured_output


def md_to_html(md_text: str) -> str:
    """Convert Markdown to HTML. Uses `markdown` lib if available, regex fallback otherwise."""
    try:
        import markdown as _md
        return _md.markdown(
            md_text,
            extensions=["tables", "fenced_code", "nl2br"],
        )
    except ImportError:
        # Minimal regex fallback
        html = md_text
        html = re.sub(r"^#### (.+)$", r"<h4>\1</h4>", html, flags=re.MULTILINE)
        html = re.sub(r"^### (.+)$",  r"<h3>\1</h3>", html, flags=re.MULTILINE)
        html = re.sub(r"^## (.+)$",   r"<h2>\1</h2>", html, flags=re.MULTILINE)
        html = re.sub(r"^# (.+)$",    r"<h1>\1</h1>", html, flags=re.MULTILINE)
        html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
        html = re.sub(r"\*(.+?)\*",     r"<em>\1</em>", html)
        html = re.sub(r"^- (.+)$",      r"<li>\1</li>", html, flags=re.MULTILINE)
        html = re.sub(r"^---$",         r"<hr>",         html, flags=re.MULTILINE)
        return f"<article>\n{html}\n</article>"


def _call_llm(prompt: str, api_key: str, model: str, system: str = "") -> str:
    """
    Modular LLM caller.
    - api_key empty OR model='mock' → returns the hydrated prompt (for UI testing)
    - model starts with 'gemini'     → Gemini via google-genai SDK
    - model starts with 'qwen'       → Qwen via OpenAI-compatible endpoint
    """
    if not api_key or model == "mock":
        time.sleep(1.2)   # simulate network latency
        return prompt     # return the hydrated prompt so the user can inspect it

    if model.startswith("gemini"):
        return _call_gemini(prompt, api_key, model, system)

    if model.startswith("qwen"):
        return _call_qwen(prompt, api_key, model, system)

    return f"[Unknown model '{model}' — check LLM settings]"


def _call_gemini(prompt: str, api_key: str, model: str, system: str) -> str:
    """Gemini via google-genai SDK. Uses the exact model string passed in."""
    try:
        from google import genai                    # type: ignore
        from google.genai import types              # type: ignore
        client = genai.Client(api_key=api_key)
        cfg = types.GenerateContentConfig(system_instruction=system) if system else None
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=cfg,
        )
        return response.text
    except Exception as exc:
        return f"[Gemini error: {exc}]"


def _call_qwen(prompt: str, api_key: str, model: str, system: str) -> str:
    """Qwen Max via Alibaba DashScope (OpenAI-compatible endpoint)."""
    try:
        from openai import OpenAI  # type: ignore
        client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        messages: list[dict] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        resp = client.chat.completions.create(model="qwen-max", messages=messages)
        return resp.choices[0].message.content
    except Exception as exc:
        return f"[Qwen error: {exc}]"


# ---------------------------------------------------------------------------
# Public stage functions (called one-by-one from geo_page.py for live progress)
# ---------------------------------------------------------------------------

def run_part0(
    inputs: dict,
    api_key: str = "",
    model: str = "mock",
    book: dict | None = None,
) -> str:
    """Stage 0 — Content Architecture Brief."""
    template = _load_prompt("seo_prompt_part0.md") or _DEFAULT_T0
    prompt   = _hydrate(template, _base_vars(inputs, book=book))
    return _call_llm(prompt, api_key, model)


def run_part1(
    inputs: dict,
    part0_output: str,
    api_key: str = "",
    model: str = "mock",
    book: dict | None = None,
) -> str:
    """Stage 1 — Article Outline."""
    template  = _load_prompt("seo_prompt_part1.md") or _DEFAULT_T1
    variables = {**_base_vars(inputs, book=book), "part0_output": part0_output}
    prompt    = _hydrate(template, variables)
    return _call_llm(prompt, api_key, model)


def run_part2(
    inputs: dict,
    part1_output: str,
    api_key: str = "",
    model: str = "mock",
    book: dict | None = None,
) -> str:
    """Stage 2 — Full Draft Production (book context + sentinel format)."""
    template  = _load_prompt("seo_prompt_part2.md") or _DEFAULT_T2
    variables = {**_base_vars(inputs, book=book), "part1_output": part1_output}
    prompt    = _hydrate(template, variables)

    if not api_key or model == "mock":
        time.sleep(1.5)
        # Return a realistic demo article so the output UI has something to show
        return _MOCK_ARTICLE.format(
            primary_kw=inputs.get("primary_kw", "your product"),
            audience=inputs.get("audience", "customers"),
        )

    return _call_llm(prompt, api_key, model)


# ---------------------------------------------------------------------------
# Convenience wrapper (for external callers / tests)
# ---------------------------------------------------------------------------

def run_chain(
    inputs: dict,
    api_key: str = "",
    model: str = "mock",
    book: dict | None = None,
) -> dict:
    """
    Convenience wrapper — runs all 3 stages and returns a fully-parsed result dict.
    geo_page.py uses the individual run_part* functions for live step-by-step progress;
    this wrapper is retained for external callers and tests.
    """
    p0 = run_part0(inputs, api_key, model, book=book)
    p1 = run_part1(inputs, p0, api_key, model, book=book)
    p2 = run_part2(inputs, p1, api_key, model, book=book)
    parsed = parse_structured_output(p2)
    return {
        "title":          parsed["title"],
        "body":           parsed["body"],
        "tech_seo":       parsed["tech_seo"],
        "part0":          p0,
        "part1":          p1,
        "part2":          p2,
        "markdown":       p2,
        "clean_markdown": parsed["body"],
        "html":           md_to_html(parsed["body"] or p2),
    }
