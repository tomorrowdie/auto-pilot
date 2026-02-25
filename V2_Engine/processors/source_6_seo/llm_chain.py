"""
Source 6 — LLM Chain for SEO Writer Engine (Epic 2)

3-stage sequential pipeline:
  Part 0 : Architecture Brief  — brand / audience / keyword context
  Part 1 : Article Outline     — section structure + H-tag plan
  Part 2 : Full Draft          — complete article, ready to publish

Each stage injects the previous stage's output invisibly as context.
Prompt templates are loaded from data/raw_zeabur_exports/seo_prompt_part{0,1,2}.md.
If the files are empty, built-in stub prompts are used automatically.

LLM caller is modular — PM will plug in Gemini / Qwen API key later.
Until then, model="mock" returns realistic demo content instantly.
"""

from __future__ import annotations

import os
import re
import time

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
_PROMPT_DIR = os.path.join(_PROJECT_ROOT, "data", "raw_zeabur_exports")


# ---------------------------------------------------------------------------
# Built-in stub prompts (used when PM prompt files are still empty)
# ---------------------------------------------------------------------------
_DEFAULT_T0 = (
    "You are an expert SEO content strategist. Produce a concise content architecture "
    "brief (300–400 words) for a high-ranking article.\n\n"
    "PRIMARY KEYWORD   : __PRIMARY_KW__\n"
    "SECONDARY KEYWORDS: __SECONDARY_KWS__\n"
    "COSMO INTENT      : __INTENT__\n"
    "BRAND             : __BRAND__\n"
    "INDUSTRY / NICHE  : __INDUSTRY__\n"
    "TARGET AUDIENCE   : __AUDIENCE__\n"
    "TONE              : __TONE__\n"
    "TARGET LENGTH     : __ARTICLE_LENGTH__ words\n\n"
    "Output: angle selection, EEAT signal plan, primary H-tag structure proposal, "
    "semantic keyword clusters to weave in."
)

_DEFAULT_T1 = (
    "Based on this content brief:\n\n"
    "--- BRIEF START ---\n"
    "__PART0_OUTPUT__\n"
    "--- BRIEF END ---\n\n"
    "Create a detailed article outline for: __PRIMARY_KW__\n\n"
    "Format: numbered H2 sections, each with 2-3 H3 sub-sections and bullet-point "
    "content directions. Include a FAQ section and a Conclusion."
)

_DEFAULT_T2 = (
    "Based on this outline:\n\n"
    "--- OUTLINE START ---\n"
    "__PART1_OUTPUT__\n"
    "--- OUTLINE END ---\n\n"
    "Write the complete, publish-ready SEO article in Markdown.\n\n"
    "Requirements:\n"
    "- Title (H1) naturally contains: __PRIMARY_KW__\n"
    "- Meta Description (italic, under title, ≤ 155 chars)\n"
    "- Introduction hooks the reader and includes the primary keyword in first 100 words\n"
    "- All outlined sections fully developed\n"
    "- Secondary keywords woven naturally: __SECONDARY_KWS__\n"
    "- COSMO intent satisfied: __INTENT__\n"
    "- FAQ section with 5 questions (use H3 for each)\n"
    "- Conclusion with a clear CTA\n"
    "- Tone: __TONE__\n"
    "- Target length: __ARTICLE_LENGTH__ words"
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


def _base_vars(inputs: dict) -> dict:
    """Build the common variable dict from inputs."""
    return {
        "primary_kw":      inputs.get("primary_kw", ""),
        "secondary_kws":   ", ".join(inputs.get("secondary_kws", [])),
        "intent":          inputs.get("intent", ""),
        "brand":           inputs.get("brand", ""),
        "industry":        inputs.get("industry", ""),
        "audience":        inputs.get("audience", "customers"),
        "tone":            inputs.get("tone", "Informative"),
        "article_length":  str(inputs.get("article_length", 1500)),
    }


def _hydrate(template: str, variables: dict) -> str:
    """Safe token replacement using __KEY__ syntax — avoids .format() KeyErrors."""
    result = template
    for key, val in variables.items():
        result = result.replace(f"__{key.upper()}__", str(val))
    return result


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
    - model='gemini-pro' / 'gemini-flash' → Gemini via google-generativeai
    - model='qwen' → Qwen via OpenAI-compatible endpoint
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
    """Gemini API via google-generativeai SDK."""
    try:
        import google.generativeai as genai  # type: ignore
        genai.configure(api_key=api_key)
        model_name = (
            "gemini-2.5-pro-preview-03-25" if "pro" in model else "gemini-2.0-flash"
        )
        kwargs = {}
        if system:
            kwargs["system_instruction"] = system
        m = genai.GenerativeModel(model_name=model_name, **kwargs)
        response = m.generate_content(prompt)
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

def run_part0(inputs: dict, api_key: str = "", model: str = "mock") -> str:
    """
    Stage 0 — Content Architecture Brief.
    Synthesises keyword + brand + audience into a strategic content brief.
    """
    template = _load_prompt("seo_prompt_part0.md") or _DEFAULT_T0
    prompt   = _hydrate(template, _base_vars(inputs))
    return _call_llm(prompt, api_key, model)


def run_part1(
    inputs: dict,
    part0_output: str,
    api_key: str = "",
    model: str = "mock",
) -> str:
    """
    Stage 1 — Article Outline.
    Takes Stage 0's brief (invisible to user) and builds a full H-tag structure.
    """
    template = _load_prompt("seo_prompt_part1.md") or _DEFAULT_T1
    variables = {**_base_vars(inputs), "part0_output": part0_output}
    prompt    = _hydrate(template, variables)
    return _call_llm(prompt, api_key, model)


def run_part2(
    inputs: dict,
    part1_output: str,
    api_key: str = "",
    model: str = "mock",
) -> str:
    """
    Stage 2 — Full Draft Production.
    Takes Stage 1's outline (invisible to user) and writes the complete article.
    In mock mode returns a realistic demo article for UI testing.
    """
    template = _load_prompt("seo_prompt_part2.md") or _DEFAULT_T2
    variables = {**_base_vars(inputs), "part1_output": part1_output}
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

def run_chain(inputs: dict, api_key: str = "", model: str = "mock") -> dict:
    """
    Run all 3 stages sequentially and return a result dict.

    Returns:
        {
            "part0":    str  — architecture brief,
            "part1":    str  — article outline,
            "part2":    str  — full draft (Markdown),
            "markdown": str  — alias for part2,
            "html":     str  — HTML-converted draft,
        }
    """
    p0 = run_part0(inputs, api_key, model)
    p1 = run_part1(inputs, p0, api_key, model)
    p2 = run_part2(inputs, p1, api_key, model)
    return {
        "part0":    p0,
        "part1":    p1,
        "part2":    p2,
        "markdown": p2,
        "html":     md_to_html(p2),
    }
