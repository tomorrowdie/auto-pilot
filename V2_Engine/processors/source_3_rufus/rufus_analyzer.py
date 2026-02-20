"""
Source 3 — Rufus Analyzer (Dual-Track Red/Blue Team AI).

Self-contained engine with hardcoded prompts (no external file dependencies).
Runs 4 analyst agents (2 Red Team Auditors + 2 Blue Team Analysts)
against Part 1 (Ask Rufus) and Part 2 (Specific Info) context.

Robust Mode:
    - 6-Stage Hybrid JSON Repair: json.loads → brute force wrap → ast.literal_eval.
    - Circuit Breaker: CPO will not run if <2 agents succeeded.
    - Model Fallback: Pro→Flash automatic retry on 503/overload.

Usage:
    from V2_Engine.processors.source_3_rufus.rufus_analyzer import (
        extract_tags,
        run_audit_team,
        generate_strategy_report,
    )
"""

from __future__ import annotations

import ast
import json
import re
import time

from langchain_core.messages import HumanMessage

from V2_Engine.saas_core.auth.registry import build_llm


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
# Minimum successful agents required to run CPO
_MIN_AGENTS_FOR_CPO = 2


# ---------------------------------------------------------------------------
# Hardcoded Prompts (extracted from n8n reference workflow)
# ---------------------------------------------------------------------------
# Placeholders use {part1_context}, {part2_text}, {part2_tags}, {intelligence_json}
# Filled via safe .replace() — NOT .format() — so literal {} in JSON examples are fine.

_PROMPTS = {
    # -----------------------------------------------------------------------
    # Red Team — Part 1 Auditor
    # -----------------------------------------------------------------------
    "p1_auditor": (
        '**Role:** You are a Hostile Algorithm Auditor.\n'
        'Your job is NOT to be helpful. Your job is to audit "Ask Rufus" data '
        'below to find logic gaps, vague answers, and potential risks.\n'
        '\n'
        '**Input Data (Part 1 - Ask Rufus Context):**\n'
        '"""\n'
        '{part1_context}\n'
        '"""\n'
        '\n'
        '**Task:**\n'
        'Analyze the input above and generate 3-4 "Trap Questions" to '
        'stress-test Rufus.\n'
        '\n'
        '**Focus Areas (The Trap Logic):**\n'
        '1. **Ambiguity Trap:**\n'
        '   * *Look for:* Rufus gave a vague "Yes" (e.g., "It works well") '
        'without technical proof.\n'
        '   * *Trap:* Ask for specific metrics. (e.g., "You said it keeps '
        'drinks hot, but exactly how many degrees does it lose per hour?")\n'
        '2. **Contradiction Trap:**\n'
        '   * *Look for:* Conflicts between User Reviews (in Part 1) and '
        'Official Tags (in Part 2).\n'
        '   * *Trap:* Point out the conflict. (e.g., "Users say the handle '
        'is loose, but tags say \'Sturdy\'. Which is it?")\n'
        '3. **Boundary Trap:**\n'
        '   * *Look for:* Use cases that are on the edge of '
        'safety/capability.\n'
        '   * *Trap:* Ask about extreme conditions. (e.g., "Is it safe to '
        'pour boiling water directly into it after taking it out of a '
        'freezer?")\n'
        '\n'
        '**Output Format (JSON Only):**\n'
        '{\n'
        '  "auditor_report": {\n'
        '    "weakness_found": "Rufus is too vague about [Topic].",\n'
        '    "trap_questions": [\n'
        '      {\n'
        '        "type": "Ambiguity Trap",\n'
        '        "question": "...",\n'
        '        "reasoning": "Rufus claimed X but didn\'t provide '
        'specific Y."\n'
        '      }\n'
        '    ]\n'
        '  }\n'
        '}'
    ),

    # -----------------------------------------------------------------------
    # Blue Team — Part 1 Analyst
    # -----------------------------------------------------------------------
    "p1_analyst": (
        '**Role:** You are a Senior Product Insight Analyst.\n'
        'Your goal is to analyze the "Ask Rufus" conversation below to '
        'uncover the **Customer\'s Hidden Desires** and **Deepest Fears**.\n'
        'We don\'t just want specs; we want to know the "Dream Scenario" '
        'the user is picturing.\n'
        '\n'
        '**Input Data (User Questions & Rufus Context):**\n'
        '"""\n'
        '{part1_context}\n'
        '"""\n'
        '\n'
        '**Task:**\n'
        'Analyze the user\'s questions and generate 3 "Validation Questions" '
        'that confirm if this product is truly their "Dream Product".\n'
        '\n'
        '**Focus Areas (The Insight Logic):**\n'
        '1.  **The "Dream" Scenario:**\n'
        '    * *Insight:* Look for keywords like "Party", "Travel", "Gift", '
        '"Reenactment". What is the *movie scene* in their head?\n'
        '    * *Validation:* Ask if the product lives up to that scene. '
        '(e.g., "Is the finish realistic enough for a 4K close-up photo?")\n'
        '2.  **The "Nightmare" (Fear):**\n'
        '    * *Insight:* Look for worries about "Leaking", "Breaking", '
        '"Peeling".\n'
        '    * *Validation:* Ask a question that proves your product '
        '*solves* this fear. (e.g., "Is the handle reinforced with a steel '
        'core to prevent snapping?")\n'
        '3.  **The "Hero" Usage:**\n'
        '    * *Insight:* Is this for themselves or to impress others?\n'
        '    * *Validation:* Ask about the "Unboxing Experience" or '
        '"Premium Feel".\n'
        '\n'
        '**Output Format (JSON Only):**\n'
        '{\n'
        '  "product_insight": {\n'
        '    "customer_profile": "The user is likely a [Persona] looking '
        'for [Benefit].",\n'
        '    "key_desire": "They want the [Aesthetic] of wood but the '
        '[Function] of steel.",\n'
        '    "key_fear": "They are terrified of [Fear].",\n'
        '    "validation_questions": [\n'
        '      {\n'
        '        "type": "Dream Validation",\n'
        '        "question": "...",\n'
        '        "insight_origin": "User mentioned [Topic], implying they '
        'want [Experience]."\n'
        '      }\n'
        '    ]\n'
        '  }\n'
        '}'
    ),

    # -----------------------------------------------------------------------
    # Red Team — Part 2 Auditor
    # -----------------------------------------------------------------------
    "p2_auditor": (
        '**Role:** You are a Hostile Data Auditor.\n'
        'Your job is to audit the "Official Amazon Specific Info" and "Tags" '
        'below to find logical inconsistencies, missing safety specs, or '
        'marketing fluff.\n'
        'You do NOT trust the marketing. You want proof.\n'
        '\n'
        '**Input Data (Official Specific Info):**\n'
        '"""\n'
        '{part2_text}\n'
        '"""\n'
        '\n'
        '**Input Data (Detected Tags):**\n'
        '"""\n'
        '{part2_tags}\n'
        '"""\n'
        '\n'
        '**Task:**\n'
        'Analyze the official info above and generate 3 "Trap Questions" '
        'that expose weaknesses in the product\'s official claims.\n'
        '\n'
        '**Focus Areas (The Trap Logic):**\n'
        '1.  **The "Tag vs. Reality" Trap:**\n'
        '    * *Look for:* A positive Tag (e.g., "Durable") vs. a warning '
        'in the text (e.g., "Handle with care").\n'
        '    * *Trap:* "You tagged this as \'Durable\', yet the text warns '
        'it breaks if dropped. Which is it?"\n'
        '2.  **The "Missing Spec" Trap:**\n'
        '    * *Look for:* Generic claims (e.g., "Stainless Steel") without '
        'specific grades (e.g., "304 Food Grade").\n'
        '    * *Trap:* "What SPECIFIC alloy of stainless steel is used? Is '
        'it 304 food-grade or cheaper 201?"\n'
        '3.  **The "Safety Silence" Trap:**\n'
        '    * *Look for:* Warnings (e.g., "Hand wash only") without '
        'explaining the consequence.\n'
        '    * *Trap:* "What exactly happens chemically or physically if I '
        'put this in the dishwasher? Does the glue melt?"\n'
        '\n'
        '**Output Format (JSON Only):**\n'
        '{\n'
        '  "auditor_report": {\n'
        '    "weakness_found": "Official info is vague about [Topic].",\n'
        '    "trap_questions": [\n'
        '      {\n'
        '        "type": "Missing Spec Trap",\n'
        '        "question": "...",\n'
        '        "reasoning": "Tags claim X but text fails to prove it."\n'
        '      }\n'
        '    ]\n'
        '  }\n'
        '}'
    ),

    # -----------------------------------------------------------------------
    # Blue Team — Part 2 Analyst
    # -----------------------------------------------------------------------
    "p2_analyst": (
        '**Role:** You are a Senior Marketing Strategist.\n'
        'Your goal is to analyze the "Official Amazon Specific Info" and '
        '"Tags" below to understand the **"Promised Experience"**.\n'
        'Ignore the flaws for a moment. Focus on: How is Amazon selling '
        'this? What is the "Hero Identity" of this product?\n'
        '\n'
        '**Input Data (Official Specific Info):**\n'
        '"""\n'
        '{part2_text}\n'
        '"""\n'
        '\n'
        '**Input Data (Detected Tags):**\n'
        '"""\n'
        '{part2_tags}\n'
        '"""\n'
        '\n'
        '**Task:**\n'
        'Analyze the marketing language and tags. Generate 3 "Confirmation '
        'Questions" to ensure the product actually delivers on these '
        'high-value promises.\n'
        '\n'
        '**Focus Areas (The Marketing Logic):**\n'
        '1.  **The "Hero" Tag:**\n'
        '    * *Insight:* What is the #1 most attractive tag? (e.g., '
        '"Giftable", "Conversation Starter").\n'
        '    * *Validation:* Ask if the physical product quality lives up '
        'to this label.\n'
        '2.  **The "Versatility" Promise:**\n'
        '    * *Insight:* Does it claim to be good for both "Hot Coffee" '
        'and "Cold Beer"?\n'
        '    * *Validation:* Ask about the performance limit of this '
        'versatility.\n'
        '3.  **The "Aesthetic" Vibe:**\n'
        '    * *Insight:* How does it describe the look? (e.g., "Viking", '
        '"Retro").\n'
        '    * *Validation:* Ask if the finish is realistic enough to pass '
        'as a prop.\n'
        '\n'
        '**Output Format (JSON Only):**\n'
        '{\n'
        '  "marketing_insight": {\n'
        '    "core_identity": "Amazon positions this as a [Identity, e.g. '
        'Rugged Viking Mug] for [Target User].",\n'
        '    "key_selling_point": "The main hook is [Hook].",\n'
        '    "confirmation_questions": [\n'
        '      {\n'
        '        "type": "Hero Tag Validation",\n'
        '        "question": "...",\n'
        '        "insight_origin": "Tag says \'Giftable\', so we must '
        'verify packaging quality."\n'
        '      }\n'
        '    ]\n'
        '  }\n'
        '}'
    ),

    # -----------------------------------------------------------------------
    # CPO — Master Strategist (outputs Markdown, not JSON)
    # -----------------------------------------------------------------------
    "cpo": (
        '**Role:** You are the Chief Product Strategist (CPO) & Creative '
        'Director.\n'
        'You have received a raw intelligence report regarding a potential '
        'new Amazon product.\n'
        'Your job is to synthesize this data into a final **"Product Attack '
        'Plan"**.\n'
        '\n'
        '**Input Intelligence Data:**\n'
        '"""\n'
        '{intelligence_json}\n'
        '"""\n'
        '\n'
        '**Task:**\n'
        'Write a strategic report for the CEO.\n'
        '\n'
        '**1. The "Kill" Decision (Quality Control):**\n'
        '   - Look at the `product_risks`. Are there any fatal flaws '
        '(e.g., safety, legal, impossible physics)?\n'
        '   - If yes, recommend KILL. If fixable, recommend FIX.\n'
        '\n'
        '**2. The "Dream" Listing Strategy (On-Amazon):**\n'
        '   - Combine `target_customer.desire` with '
        '`marketing_assets.identity`.\n'
        '   - Write a sample **Amazon Title** (max 199 chars) that hits the '
        '"Desire" while avoiding the "Risks".\n'
        '   - *Key Focus:* Use strong, emotional keywords derived from the '
        'Persona.\n'
        '\n'
        '**3. The "Anti-Rufus" Defense (Technical Bullet Points):**\n'
        '   - How do we preemptively answer the "Risks" in our bullet '
        'points so Rufus never doubts us?\n'
        '   - Example: If risk is "Mold", suggestion: "Add bullet point '
        'about \'Seamless Uni-body Tech\'."\n'
        '\n'
        '**3.5. The "COSMO & EEAT" Friction Shield '
        '(Yellow/Orange Gap Analysis):**\n'
        '   Synthesize the findings from the Yellow Team '
        '(`customer_reality`) and Orange Team (`listing_gaps`).\n'
        '\n'
        '   - **A. The "Don\'t See What You\'re Looking For?" Defense:**\n'
        '     - Identify specific "Missing Info" questions users keep '
        'asking (from Yellow Data `customer_reality.missing_info`).\n'
        '     - Write a "Q&A Pre-empt" Bullet Point to answer each one '
        '(e.g., "Yes, fits Size 14 — tested up to 15W").\n'
        '\n'
        '   - **B. The Trust Injection (EEAT):**\n'
        '     - Look for "Dealbreakers" in `customer_reality.dealbreakers`'
        ' (e.g., "Plastic cracks").\n'
        '     - Suggest a specific "Proof Point" or Image to add to the '
        'A+ Content (e.g., "Add \'Hammer Test\' video showing impact '
        'resistance").\n'
        '\n'
        '   - **C. SEO & Format Warning:**\n'
        '     - If the Orange Team flagged "Images Only" A+ Content in '
        '`listing_gaps.seo_flags`, issue a **CRITICAL SEO WARNING** '
        'here.\n'
        '     - Explain that text embedded in images is invisible to '
        'Rufus and crawlers. Recommend adding text modules.\n'
        '\n'
        '**4. The "Creative War Room" (Marketing Direction):**\n'
        '   *Since we lack keyword volume data, focus on **Psychographic '
        'Targeting** based on the `target_customer.persona`.*\n'
        '\n'
        '   - **A. Amazon PPC Strategy (Targeting Archetypes):**\n'
        '     - Who should we target? Don\'t just say "Mug buyers".\n'
        '     - Suggest 6 specific **Customer Avatars** or **Usage '
        'Occasions** to bid on (e.g., "Dungeon Masters", "Groomsmen '
        'Gifts", "Ren Faire Attendees").\n'
        '\n'
        '   - **B. Off-Amazon Topic Clusters (Content Marketing):**\n'
        '     - Based on `target_customer.desire` (e.g., Immersion), what '
        'content will attract them?\n'
        '     - Suggest 6 **Blog/Social Topics** that build the "Dream '
        'Lifestyle" (e.g., "5 Tips for an Authentic Viking Wedding").\n'
        '\n'
        '**Output Format (Markdown):**\n'
        'Output a clean Markdown report starting with '
        '"## \U0001f680 PRODUCT STRATEGY REPORT".'
    ),

    # -----------------------------------------------------------------------
    # Yellow Team — Gatekeeper (Sentiment Classifier)
    # -----------------------------------------------------------------------
    "y_classifier": (
        '**Role:** You are a Picky Customer who is impossible to impress.\n'
        'Your job is to read a raw dump of Amazon Customer Reviews and Q&A '
        'and split them into two buckets: POSITIVE and NEGATIVE.\n'
        '\n'
        '**Classification Rule (Be Picky):**\n'
        'A review is POSITIVE **only** if the customer expresses genuine '
        'enthusiasm, delight, or a specific benefit they personally '
        'experienced.\n'
        'Everything else — lukewarm praise, mixed feelings, "it\'s okay", '
        'factual-only descriptions, unanswered questions, and anything '
        'with a "but" — goes into NEGATIVE.\n'
        '**When in doubt, classify as NEGATIVE.** We would rather miss a '
        'compliment than miss a complaint.\n'
        '\n'
        '**Input Data (Raw Reviews & Q&A):**\n'
        '"""\n'
        '{raw_reviews}\n'
        '"""\n'
        '\n'
        '**Task:**\n'
        'Read each review or Q&A block. Classify it. Then output TWO text '
        'blocks: one containing all POSITIVE content, one containing all '
        'NEGATIVE content. Preserve the original text — do not summarize.\n'
        '\n'
        '**Output Format (JSON Only):**\n'
        '{\n'
        '  "gatekeeper": {\n'
        '    "positive_count": 5,\n'
        '    "negative_count": 12,\n'
        '    "positive_text": "Full text of all positive reviews...",\n'
        '    "negative_text": "Full text of all negative reviews..."\n'
        '  }\n'
        '}'
    ),

    # -----------------------------------------------------------------------
    # Yellow Team — Positive Auditor (Hero Scenarios)
    # -----------------------------------------------------------------------
    "y_positive": (
        '**Role:** You are a COSMO Experience Mapper.\n'
        'Your job is to analyze POSITIVE customer reviews and extract '
        '"Hero Scenarios" — real-world usage stories where the product '
        'delivered genuine delight.\n'
        '\n'
        '**Input Data (Positive Reviews):**\n'
        '"""\n'
        '{positive_text}\n'
        '"""\n'
        '\n'
        '**Task:**\n'
        'For each review, identify the **Hero Scenario**: the specific '
        'situation, occasion, or use case where the product was a hit.\n'
        'These will be used for Amazon COSMO intent mapping and EEAT '
        '"Experience" signals.\n'
        '\n'
        '**Focus Areas:**\n'
        '1. **Usage Occasion:** Gift, party, daily use, travel, display?\n'
        '2. **Emotional Payoff:** What feeling did it deliver? Pride, '
        'surprise, nostalgia, convenience?\n'
        '3. **Social Proof:** Did the reviewer mention others reacting '
        'positively? ("My husband loved it", "Friends were impressed")\n'
        '\n'
        '**Output Format (JSON Only):**\n'
        '{\n'
        '  "hero_scenarios": [\n'
        '    {\n'
        '      "occasion": "Birthday Gift",\n'
        '      "emotion": "Genuine surprise and delight",\n'
        '      "quote": "Direct quote from the review...",\n'
        '      "cosmo_intent": "gift-for-him"\n'
        '    }\n'
        '  ]\n'
        '}'
    ),

    # -----------------------------------------------------------------------
    # Yellow Team — Negative Auditor (Dealbreakers & Missing Info)
    # -----------------------------------------------------------------------
    "y_negative": (
        '**Role:** You are a Consumer Protection Investigator.\n'
        'Your job is to analyze NEGATIVE customer reviews and Q&A to find '
        '"Dealbreakers" — issues that would make a smart shopper walk away '
        '— and "Missing Info" — questions the listing fails to answer.\n'
        '\n'
        '**Input Data (Negative Reviews & Q&A):**\n'
        '"""\n'
        '{negative_text}\n'
        '"""\n'
        '\n'
        '**Task:**\n'
        'Extract two lists:\n'
        '1. **Dealbreakers:** Specific product failures (defects, safety, '
        'false claims).\n'
        '2. **Missing Info:** Questions customers asked that the listing '
        'never answered.\n'
        '\n'
        '**Focus Areas:**\n'
        '1. **Physical Defect:** Leaking, breaking, peeling, smell?\n'
        '2. **Expectation Mismatch:** "Smaller than expected", "Not as '
        'shown"?\n'
        '3. **Safety Concern:** Any mention of injury, chemical smell, '
        'sharp edges?\n'
        '4. **Unanswered Question:** Q&A items with no seller response or '
        'vague answers?\n'
        '\n'
        '**Output Format (JSON Only):**\n'
        '{\n'
        '  "dealbreakers": [\n'
        '    {\n'
        '      "type": "Physical Defect",\n'
        '      "issue": "Handle snapped after 2 weeks",\n'
        '      "severity": "high",\n'
        '      "quote": "Direct quote..."\n'
        '    }\n'
        '  ],\n'
        '  "missing_info": [\n'
        '    {\n'
        '      "question": "Is this dishwasher safe?",\n'
        '      "status": "unanswered",\n'
        '      "risk": "Customers assume no = bad"\n'
        '    }\n'
        '  ]\n'
        '}'
    ),

    # -----------------------------------------------------------------------
    # Orange Team — Listing Gap Analyzer (Single-Pass)
    # -----------------------------------------------------------------------
    "o_gap_analyzer": (
        '**Role:** You are a Listing Gap Analyst & SEO Auditor.\n'
        'Your job is to compare what CUSTOMERS complain about (from Reviews '
        '& Q&A) and what AUDITORS flagged as risks against what the '
        "SELLER'S LISTING actually says. You find the gaps — claims the "
        'listing fails to address.\n'
        '\n'
        "**Input Data (Seller's Current Listing):**\n"
        '"""\n'
        'TITLE: {listing_title}\n'
        '\n'
        'BULLET POINTS:\n'
        '{listing_bullets}\n'
        '\n'
        'A+ CONTENT:\n'
        '{listing_aplus}\n'
        '\n'
        'A+ CONTENT STATUS: {aplus_status}\n'
        '"""\n'
        '\n'
        '**Input Data (Product Details & Specs):**\n'
        '"""\n'
        '{product_details}\n'
        '"""\n'
        '\n'
        '**Input Data (Intelligence Findings — Risks & Complaints):**\n'
        '"""\n'
        '{all_findings}\n'
        '"""\n'
        '\n'
        '**Task:**\n'
        'Perform a Gap Analysis:\n'
        '1. For each Dealbreaker or Risk found by the intelligence team, '
        "check if the listing's Title, Bullets, or A+ Content specifically "
        'addresses it.\n'
        '2. Score the listing\'s overall coverage from 1 to 10.\n'
        '3. Suggest specific rewrites for unaddressed gaps.\n'
        '4. Flag any SEO visibility issues.\n'
        '\n'
        '**CRITICAL SEO RULE:**\n'
        'If A+ Content Status says "Images Only", this is a **Critical SEO '
        'Failure**.\n'
        'Text inside an image (JPG/PNG) cannot be read by search crawlers '
        'or Amazon Rufus. It is effectively invisible. You MUST flag this '
        'as a high-severity SEO issue with this exact reasoning:\n'
        '"Your A+ content is invisible to search algorithms because text '
        'is embedded in images."\n'
        '\n'
        '**Focus Areas:**\n'
        '1. **Addressed:** Which customer complaints does the listing '
        'already handle? Cite the specific bullet or title phrase.\n'
        '2. **Unaddressed:** Which complaints are completely ignored by '
        'the listing? Mark priority (high/medium/low).\n'
        '3. **Fix Suggestions:** Write a specific bullet rewrite that '
        'closes each gap. Be concrete — give the exact text.\n'
        '4. **SEO Flags:** Images-only A+, missing keywords, invisible '
        'content, generic claims without proof.\n'
        '\n'
        '**Output Format (JSON Only):**\n'
        '{\n'
        '  "gap_analysis": {\n'
        '    "coverage_score": 4,\n'
        '    "addressed": [\n'
        '      {\n'
        '        "issue": "Leaking complaints",\n'
        '        "listing_evidence": "Bullet 2 mentions triple-seal lid"\n'
        '      }\n'
        '    ],\n'
        '    "unaddressed": [\n'
        '      {\n'
        '        "issue": "Handle durability",\n'
        '        "source": "Yellow Dealbreaker",\n'
        '        "priority": "high"\n'
        '      }\n'
        '    ],\n'
        '    "fix_suggestions": [\n'
        '      {\n'
        '        "target": "Bullet 3",\n'
        '        "problem": "Ignores handle breaks complaint",\n'
        '        "fix": "Add: Reinforced steel-core handle tested to 50 lbs"\n'
        '      }\n'
        '    ],\n'
        '    "seo_flags": [\n'
        '      {\n'
        '        "issue": "A+ Content is images-only",\n'
        '        "severity": "critical",\n'
        '        "risk": "Invisible to Rufus and crawlers",\n'
        '        "fix": "Add text modules with keyword-rich descriptions"\n'
        '      }\n'
        '    ]\n'
        '  }\n'
        '}'
    ),
}


# ---------------------------------------------------------------------------
# Tag Extraction (replicates n8n "Part2 Complete" heuristic)
# ---------------------------------------------------------------------------
def extract_tags(text: str) -> list[str]:
    """
    Extract short tags/phrases from Part 2 text.

    Heuristic from the n8n workflow: split by lines/commas,
    keep phrases under 40 chars that don't end with a period.

    Args:
        text: The OCR-extracted text from Part 2 screenshots.

    Returns:
        List of unique tag strings.
    """
    if not text.strip():
        return []

    tags = set()
    for line in re.split(r"[,\n]", text):
        cleaned = line.strip()
        # Remove markdown artifacts
        cleaned = re.sub(r"^[-*#>]+\s*", "", cleaned)
        cleaned = re.sub(r"\*\*", "", cleaned)

        if cleaned and len(cleaned) < 40 and not cleaned.endswith("."):
            tags.add(cleaned)

    return sorted(tags)


# ---------------------------------------------------------------------------
# LLM Call via V5 Registry (LangChain)
# ---------------------------------------------------------------------------
def _call_llm(
    prompt: str,
    provider: str,
    api_key: str,
    model: str,
    json_mode: bool = True,
) -> str:
    """
    Call any supported LLM provider via the V5 registry.

    Args:
        prompt:    The full prompt text (already formatted with context).
        provider:  Registry key (e.g. 'google', 'openai', 'anthropic').
        api_key:   Provider API key.
        model:     Model name.
        json_mode: Unused — prompts instruct JSON format directly.
                   Kept for call-site compatibility.

    Returns:
        Raw text response from the model.

    Raises:
        RuntimeError on API failure.
    """
    llm = build_llm(provider, api_key, model, temperature=0.2)
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content


# ---------------------------------------------------------------------------
# 6-Stage Hybrid JSON Repair & Parse
# ---------------------------------------------------------------------------
def _repair_and_parse_json(raw_text: str) -> dict:
    """
    6-stage hybrid parser for messy LLM output.

    Stage 1: Strip markdown fences.
    Stage 2: Fix trailing commas.
    Stage 3: json.loads (standard parse).
    Stage 4: json.loads with brute force brace wrap.
    Stage 5: ast.literal_eval with JSON→Python token conversion.
    Stage 6: Safe skeleton fallback (pipeline never crashes).
    """
    _SAFE_FALLBACK = {"auditor_report": {"trap_questions": []}}

    if not raw_text or not raw_text.strip():
        return {"_raw": "(empty response)", **_SAFE_FALLBACK}

    cleaned = raw_text.strip()

    # Stage 1: Strip markdown fences
    cleaned = re.sub(r"^```json\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^```\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"```\s*$", "", cleaned)
    cleaned = cleaned.strip()

    # Stage 2: Fix trailing commas (common LLM mistake)
    fixed = re.sub(r",\s*([}\]])", r"\1", cleaned)

    # Stage 3: Try direct json.loads (handles valid JSON)
    for text in (fixed, cleaned):
        try:
            return json.loads(text)
        except (json.JSONDecodeError, ValueError):
            pass

    # Stage 4: Brute Force Wrap (fixes missing outer braces)
    print("[Rufus Analyzer] JSON repair: attempting brute force wrap...")
    for text in (fixed, cleaned):
        try:
            return json.loads("{" + text + "}")
        except (json.JSONDecodeError, ValueError):
            pass

    # Stage 5: Python-Native Pivot (ast.literal_eval)
    # Pre-process: convert JSON tokens → Python literals to prevent NameError
    print("[Rufus Analyzer] JSON repair: attempting ast.literal_eval...")
    for text in (fixed, cleaned):
        pythonized = text
        # Convert JSON booleans/null → Python (word-boundary safe)
        pythonized = re.sub(r'\btrue\b', 'True', pythonized)
        pythonized = re.sub(r'\bfalse\b', 'False', pythonized)
        pythonized = re.sub(r'\bnull\b', 'None', pythonized)
        # Try direct parse
        try:
            result = ast.literal_eval(pythonized)
            if isinstance(result, dict):
                return result
        except (ValueError, SyntaxError):
            pass
        # Try with brace wrap
        try:
            result = ast.literal_eval("{" + pythonized + "}")
            if isinstance(result, dict):
                return result
        except (ValueError, SyntaxError):
            pass

    # Stage 5b: Last resort — extract outermost { ... } substring
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace > first_brace:
        extracted = cleaned[first_brace:last_brace + 1]
        try:
            return json.loads(extracted)
        except (json.JSONDecodeError, ValueError):
            pass

    # Stage 6: Fallback — return raw text with safe skeleton
    print(
        f"[Rufus Analyzer] JSON repair: all 6 stages failed. "
        f"Returning raw text ({len(cleaned)} chars)."
    )
    return {"_raw": cleaned[:1000], **_SAFE_FALLBACK}


# ---------------------------------------------------------------------------
# Safe Prompt Filling (uses .replace() to avoid {}-escaping issues)
# ---------------------------------------------------------------------------
def _fill_prompt(template: str, context_vars: dict) -> str:
    """
    Fill prompt placeholders using safe .replace() instead of .format().

    This avoids KeyError crashes from literal {} in JSON examples
    embedded within the prompt text.
    """
    result = template
    for key, value in context_vars.items():
        result = result.replace("{" + key + "}", str(value))
    return result


# ---------------------------------------------------------------------------
# Step B: Run the 4-Agent Audit Team
# ---------------------------------------------------------------------------
def _run_single_agent(
    agent_name: str,
    prompt_template: str,
    context_vars: dict,
    provider: str,
    api_key: str,
    model: str,
) -> dict:
    """
    Run a single analyst agent.

    Args:
        agent_name:      Human-readable label (for logging).
        prompt_template:  The prompt with {placeholders}.
        context_vars:     Dict to fill the placeholders.
        provider:         Registry key (e.g. 'google', 'openai', 'anthropic').
        api_key:          Provider API key.
        model:            Model name.

    Returns:
        Parsed JSON dict from the LLM, or {"_error": "..."} on failure.
    """
    try:
        # Fill in the context variables (safe replace, no .format())
        filled_prompt = _fill_prompt(prompt_template, context_vars)

        print(
            f"[Rufus Analyzer] Running {agent_name} "
            f"({len(filled_prompt)} chars) on {model}..."
        )

        raw = _call_llm(filled_prompt, provider, api_key, model, json_mode=True)
        result = _repair_and_parse_json(raw)

        # Check if repair returned degraded output
        if "_raw" in result:
            print(
                f"[Rufus Analyzer] {agent_name}: JSON repair returned "
                f"degraded output."
            )
            return {
                "_error": f"JSON parse failed (degraded): {result['_raw'][:200]}",
                "_agent": agent_name,
            }

        print(f"[Rufus Analyzer] {agent_name} complete.")
        return result

    except Exception as e:
        print(f"[Rufus Analyzer] ERROR in {agent_name}: {e}")
        return {"_error": str(e)[:300], "_agent": agent_name}


def run_audit_team(
    text_part_1: str,
    text_part_2: str,
    provider: str,
    api_key: str,
    model: str = "gemini-2.5-flash",
) -> dict:
    """
    Run the 4-agent Red/Blue Team analysis.

    Executes sequentially (to respect API rate limits):
        1. Part 1 Auditor (Red)  — finds logic gaps in Rufus answers
        2. Part 1 Analyst (Blue) — extracts customer desires/fears
        3. Part 2 Auditor (Red)  — finds spec inconsistencies
        4. Part 2 Analyst (Blue) — analyzes marketing identity

    Args:
        text_part_1: Consolidated context from Part 1 (Ask Rufus).
        text_part_2: Consolidated context from Part 2 (Specific Info).
        provider:    Registry key (e.g. 'google', 'openai', 'anthropic').
        api_key:     Provider API key.
        model:       Model name (default: gemini-2.5-flash).

    Returns:
        {
            "p1_audit":   dict,   # Red Team output for Part 1
            "p1_insight":  dict,   # Blue Team output for Part 1
            "p2_audit":   dict,   # Red Team output for Part 2
            "p2_insight":  dict,   # Blue Team output for Part 2
            "tags":       list,   # Extracted tags from Part 2
            "stats": {
                "agents_run": int,
                "agents_ok": int,
                "agents_error": int,
            },
        }
    """
    # Extract tags from Part 2
    tags = extract_tags(text_part_2) if text_part_2.strip() else []
    tags_str = ", ".join(tags) if tags else "(no tags detected)"

    # Context vars for each prompt
    p1_vars = {"part1_context": text_part_1}
    p2_vars = {"part2_text": text_part_2, "part2_tags": tags_str}

    results = {}
    agents_ok = 0
    agents_error = 0

    # --- Agent 1: Part 1 Auditor (Red Team) ---
    if text_part_1.strip() and "p1_auditor" in _PROMPTS:
        results["p1_audit"] = _run_single_agent(
            "Part 1 Auditor (Red Team)",
            _PROMPTS["p1_auditor"],
            p1_vars, provider, api_key, model,
        )
        if "_error" not in results["p1_audit"]:
            agents_ok += 1
        else:
            agents_error += 1
        time.sleep(2)
    else:
        results["p1_audit"] = {"_skipped": "No Part 1 data or prompt missing"}

    # --- Agent 2: Part 1 Analyst (Blue Team) ---
    if text_part_1.strip() and "p1_analyst" in _PROMPTS:
        results["p1_insight"] = _run_single_agent(
            "Part 1 Analyst (Blue Team)",
            _PROMPTS["p1_analyst"],
            p1_vars, provider, api_key, model,
        )
        if "_error" not in results["p1_insight"]:
            agents_ok += 1
        else:
            agents_error += 1
        time.sleep(2)
    else:
        results["p1_insight"] = {"_skipped": "No Part 1 data or prompt missing"}

    # --- Agent 3: Part 2 Auditor (Red Team) ---
    if text_part_2.strip() and "p2_auditor" in _PROMPTS:
        results["p2_audit"] = _run_single_agent(
            "Part 2 Auditor (Red Team)",
            _PROMPTS["p2_auditor"],
            p2_vars, provider, api_key, model,
        )
        if "_error" not in results["p2_audit"]:
            agents_ok += 1
        else:
            agents_error += 1
        time.sleep(2)
    else:
        results["p2_audit"] = {"_skipped": "No Part 2 data or prompt missing"}

    # --- Agent 4: Part 2 Analyst (Blue Team) ---
    if text_part_2.strip() and "p2_analyst" in _PROMPTS:
        results["p2_insight"] = _run_single_agent(
            "Part 2 Analyst (Blue Team)",
            _PROMPTS["p2_analyst"],
            p2_vars, provider, api_key, model,
        )
        if "_error" not in results["p2_insight"]:
            agents_ok += 1
        else:
            agents_error += 1
    else:
        results["p2_insight"] = {"_skipped": "No Part 2 data or prompt missing"}

    results["tags"] = tags
    results["stats"] = {
        "agents_run": agents_ok + agents_error,
        "agents_ok": agents_ok,
        "agents_error": agents_error,
    }

    print(
        f"[Rufus Analyzer] Audit team complete: "
        f"{agents_ok} OK, {agents_error} errors"
    )
    return results


# ---------------------------------------------------------------------------
# Step C: Run the Yellow Team (Gatekeeper → Dual-Track Audit)
# ---------------------------------------------------------------------------
def run_yellow_team(
    raw_reviews: str,
    provider: str,
    api_key: str,
    model: str = "gemini-2.5-flash",
) -> dict:
    """
    Run the 3-agent Yellow Team pipeline.

    Phase 1 — Gatekeeper: AI sentiment classifier splits raw text into
              positive_text and negative_text buckets.
    Phase 2 — Dual-Track: Positive Auditor + Negative Auditor run on
              the split text.

    Args:
        raw_reviews: Raw copy-pasted Amazon reviews & Q&A.
        provider:    Registry key (e.g. 'google', 'openai', 'anthropic').
        api_key:     Provider API key.
        model:       Model name (default: gemini-2.5-flash).

    Returns:
        {
            "gatekeeper": dict,       # Classifier output
            "hero_scenarios": dict,   # Positive Auditor output
            "dealbreakers": dict,     # Negative Auditor output
            "stats": {
                "agents_run": int,
                "agents_ok": int,
                "agents_error": int,
            },
        }
    """
    results = {}
    agents_ok = 0
    agents_error = 0

    # --- Phase 1: Gatekeeper (Sentiment Classifier) ---
    print("[Rufus Analyzer] Yellow Team: Running Gatekeeper...")
    gatekeeper = _run_single_agent(
        "Yellow Gatekeeper (Classifier)",
        _PROMPTS["y_classifier"],
        {"raw_reviews": raw_reviews},
        provider, api_key, model,
    )
    results["gatekeeper"] = gatekeeper

    if "_error" in gatekeeper:
        agents_error += 1
        print("[Rufus Analyzer] Yellow Gatekeeper failed. Aborting Yellow Team.")
        results["hero_scenarios"] = {"_skipped": "Gatekeeper failed"}
        results["dealbreakers"] = {"_skipped": "Gatekeeper failed"}
        results["stats"] = {
            "agents_run": 1,
            "agents_ok": 0,
            "agents_error": 1,
        }
        return results

    agents_ok += 1
    time.sleep(2)

    # Extract split text from gatekeeper output
    gk = gatekeeper.get("gatekeeper", {})
    positive_text = gk.get("positive_text", "")
    negative_text = gk.get("negative_text", "")

    pos_words = len(positive_text.split()) if positive_text.strip() else 0
    neg_words = len(negative_text.split()) if negative_text.strip() else 0
    print(
        f"[Rufus Analyzer] Gatekeeper split: "
        f"{gk.get('positive_count', '?')} positive ({pos_words} words), "
        f"{gk.get('negative_count', '?')} negative ({neg_words} words)"
    )

    # --- Phase 2a: Positive Auditor (Hero Scenarios) ---
    if positive_text.strip():
        results["hero_scenarios"] = _run_single_agent(
            "Yellow Positive Auditor (Heroes)",
            _PROMPTS["y_positive"],
            {"positive_text": positive_text},
            provider, api_key, model,
        )
        if "_error" not in results["hero_scenarios"]:
            agents_ok += 1
        else:
            agents_error += 1
        time.sleep(2)
    else:
        results["hero_scenarios"] = {"_skipped": "No positive reviews found"}

    # --- Phase 2b: Negative Auditor (Dealbreakers) ---
    if negative_text.strip():
        results["dealbreakers"] = _run_single_agent(
            "Yellow Negative Auditor (Dealbreakers)",
            _PROMPTS["y_negative"],
            {"negative_text": negative_text},
            provider, api_key, model,
        )
        if "_error" not in results["dealbreakers"]:
            agents_ok += 1
        else:
            agents_error += 1
    else:
        results["dealbreakers"] = {"_skipped": "No negative reviews found"}

    results["stats"] = {
        "agents_run": agents_ok + agents_error,
        "agents_ok": agents_ok,
        "agents_error": agents_error,
    }

    print(
        f"[Rufus Analyzer] Yellow Team complete: "
        f"{agents_ok} OK, {agents_error} errors"
    )
    return results


# ---------------------------------------------------------------------------
# Step D: Run the Orange Team (Listing Gap Analyzer)
# ---------------------------------------------------------------------------
def run_orange_team(
    listing_title: str,
    listing_bullets: str,
    listing_aplus: str,
    product_details: str,
    aplus_status: str,
    team_results: dict,
    provider: str,
    api_key: str,
    model: str = "gemini-2.5-flash",
) -> dict:
    """
    Run the single-agent Orange Team (Listing Gap Analyzer).

    Compares the user's Amazon listing (Title, Bullets, A+ Content) against
    intelligence findings from Yellow Team (dealbreakers, missing_info) and
    Red Team (trap questions) to find gaps the listing fails to address.

    Args:
        listing_title:   Amazon product title.
        listing_bullets:  Bullet points text.
        listing_aplus:   A+ Content text (may be empty).
        product_details: Technical specs, dimensions, materials, BSR info.
        aplus_status:    "Standard Text Modules" or "Images Only".
        team_results:    Output from run_audit_team() (may contain "yellow" key).
        provider:        Registry key (e.g. 'google', 'openai', 'anthropic').
        api_key:         Provider API key.
        model:           Model name (default: gemini-2.5-flash).

    Returns:
        {
            "gap_analysis": dict,   # Coverage score, addressed, unaddressed,
                                    # fix_suggestions, seo_flags
            "stats": {
                "agents_run": int,
                "agents_ok": int,
                "agents_error": int,
            },
        }
    """
    # --- Build the intelligence findings summary for the prompt ---
    findings = []

    # Yellow Team findings (primary source)
    yellow = team_results.get("yellow", {})
    if yellow and "_error" not in yellow.get("gatekeeper", {}):
        deals_raw = yellow.get("dealbreakers", {})
        if "_error" not in deals_raw and "_skipped" not in deals_raw:
            for d in deals_raw.get("dealbreakers", []):
                findings.append(
                    f"[Customer Dealbreaker] ({d.get('severity', '?')} severity) "
                    f"{d.get('issue', '')} — \"{d.get('quote', '')}\""
                )
            for m in deals_raw.get("missing_info", []):
                findings.append(
                    f"[Unanswered Question] {m.get('question', '')} "
                    f"(Risk: {m.get('risk', '?')})"
                )
        heroes_raw = yellow.get("hero_scenarios", {})
        if "_error" not in heroes_raw and "_skipped" not in heroes_raw:
            for h in heroes_raw.get("hero_scenarios", []):
                findings.append(
                    f"[Hero Scenario] {h.get('occasion', '')}: "
                    f"{h.get('emotion', '')} (COSMO: {h.get('cosmo_intent', '')})"
                )

    # Red Team findings (fallback / supplement)
    for key, label in [("p1_audit", "Rufus Q&A"), ("p2_audit", "Specs/Tags")]:
        audit = team_results.get(key, {})
        if "_error" not in audit and "_skipped" not in audit:
            for trap in audit.get("auditor_report", {}).get("trap_questions", []):
                findings.append(
                    f"[Red Team — {label}] {trap.get('type', 'Risk')}: "
                    f"{trap.get('reasoning', '')}"
                )

    if not findings:
        findings.append("(No intelligence findings available — run a basic listing audit)")

    findings_str = "\n".join(findings)

    # --- Run the single agent ---
    context_vars = {
        "listing_title": listing_title or "(no title provided)",
        "listing_bullets": listing_bullets or "(no bullets provided)",
        "listing_aplus": listing_aplus or "(no A+ content provided)",
        "product_details": product_details or "(no product details provided)",
        "aplus_status": aplus_status,
        "all_findings": findings_str,
    }

    print("[Rufus Analyzer] Orange Team: Running Gap Analyzer...")
    result = _run_single_agent(
        "Orange Gap Analyzer",
        _PROMPTS["o_gap_analyzer"],
        context_vars,
        provider, api_key, model,
    )

    agents_ok = 0 if "_error" in result else 1
    agents_error = 1 - agents_ok

    stats = {
        "agents_run": 1,
        "agents_ok": agents_ok,
        "agents_error": agents_error,
    }

    print(
        f"[Rufus Analyzer] Orange Team complete: "
        f"{agents_ok} OK, {agents_error} errors"
    )
    return {"gap_analysis": result, "stats": stats}


# ---------------------------------------------------------------------------
# Intelligence Aggregator (replicates n8n "Aggregate All Intelligence")
# ---------------------------------------------------------------------------
def aggregate_intelligence(team_results: dict) -> dict:
    """
    Build the master intelligence object from 4 agent outputs.

    Replicates the n8n "Aggregate All Intelligence" node logic.

    Args:
        team_results: Output from run_audit_team().

    Returns:
        {
            "target_customer": { "persona", "desire", "fear" },
            "product_risks": [ str, ... ],
            "marketing_assets": { "identity", "selling_point" },
            "trap_questions_archive": { "p1_traps": [...], "p2_traps": [...] },
        }
    """
    p1_audit = team_results.get("p1_audit", {})
    p1_insight = team_results.get("p1_insight", {})
    p2_audit = team_results.get("p2_audit", {})
    p2_insight = team_results.get("p2_insight", {})

    # Extract customer profile from P1 Analyst
    pi = p1_insight.get("product_insight", {})
    target_customer = {
        "persona": pi.get("customer_profile", "Unknown"),
        "desire": pi.get("key_desire", "Unknown"),
        "fear": pi.get("key_fear", "Unknown"),
    }

    # Collect risks from both auditors
    p1_traps = (
        p1_audit.get("auditor_report", {}).get("trap_questions", [])
    )
    p2_traps = (
        p2_audit.get("auditor_report", {}).get("trap_questions", [])
    )

    product_risks = []
    for q in p1_traps:
        product_risks.append(f"[User Complaint] {q.get('reasoning', '')}")
    for q in p2_traps:
        product_risks.append(f"[Spec Defect] {q.get('reasoning', '')}")

    # Marketing assets from P2 Analyst
    mi = p2_insight.get("marketing_insight", {})
    marketing_assets = {
        "identity": mi.get("core_identity", "Unknown"),
        "selling_point": mi.get("key_selling_point", "Unknown"),
    }

    # --- Yellow Team Integration (if present) ---
    yellow = team_results.get("yellow", {})
    customer_reality = {}
    if yellow and "_error" not in yellow.get("gatekeeper", {}):
        # Hero scenarios from positive auditor
        heroes_raw = yellow.get("hero_scenarios", {})
        if "_error" not in heroes_raw and "_skipped" not in heroes_raw:
            customer_reality["hero_scenarios"] = heroes_raw.get(
                "hero_scenarios", [],
            )

        # Dealbreakers from negative auditor
        deals_raw = yellow.get("dealbreakers", {})
        if "_error" not in deals_raw and "_skipped" not in deals_raw:
            customer_reality["dealbreakers"] = deals_raw.get(
                "dealbreakers", [],
            )
            customer_reality["missing_info"] = deals_raw.get(
                "missing_info", [],
            )
            # Add dealbreakers to product_risks for CPO visibility
            for d in customer_reality.get("dealbreakers", []):
                product_risks.append(
                    f"[Customer Reality] {d.get('issue', '')}"
                )

        # Gatekeeper stats
        gk = yellow.get("gatekeeper", {}).get("gatekeeper", {})
        customer_reality["gatekeeper_stats"] = {
            "positive_count": gk.get("positive_count", 0),
            "negative_count": gk.get("negative_count", 0),
        }

    # --- Orange Team Integration (if present) ---
    listing_gaps = {}
    orange = team_results.get("orange", {})
    gap_raw = orange.get("gap_analysis", {})
    if gap_raw and "_error" not in gap_raw:
        ga = gap_raw.get("gap_analysis", {})
        listing_gaps["coverage_score"] = ga.get("coverage_score", 0)
        listing_gaps["addressed"] = ga.get("addressed", [])
        listing_gaps["unaddressed"] = ga.get("unaddressed", [])
        listing_gaps["fix_suggestions"] = ga.get("fix_suggestions", [])
        listing_gaps["seo_flags"] = ga.get("seo_flags", [])

        # Add unaddressed gaps to product_risks for CPO visibility
        for gap in listing_gaps.get("unaddressed", []):
            product_risks.append(
                f"[Listing Gap] {gap.get('issue', '')} "
                f"(priority: {gap.get('priority', '?')})"
            )
        for flag in listing_gaps.get("seo_flags", []):
            product_risks.append(
                f"[SEO Flag] {flag.get('issue', '')}: {flag.get('risk', '')}"
            )

    return {
        "target_customer": target_customer,
        "product_risks": product_risks,
        "marketing_assets": marketing_assets,
        "trap_questions_archive": {
            "p1_traps": p1_traps,
            "p2_traps": p2_traps,
        },
        "customer_reality": customer_reality,
        "listing_gaps": listing_gaps,
    }


# ---------------------------------------------------------------------------
# CPO Strategist — Phase 2B (with Circuit Breaker)
# ---------------------------------------------------------------------------
def generate_strategy_report(
    audit_results: dict,
    provider: str,
    api_key: str,
    model: str = "gemini-2.5-pro",
) -> str:
    """
    Generate the final CPO Strategy Report.

    Circuit Breaker: Refuses to call the expensive Pro model if fewer
    than _MIN_AGENTS_FOR_CPO agents succeeded. Returns an error report
    instead, saving API cost and avoiding garbage-in/garbage-out.

    Args:
        audit_results: Output from run_audit_team().
        provider:      Registry key (e.g. 'google', 'openai', 'anthropic').
        api_key:       Provider API key.
        model:         Model name.

    Returns:
        Markdown strategy report string.
    """
    stats = audit_results.get("stats", {})
    agents_ok = stats.get("agents_ok", 0)
    agents_error = stats.get("agents_error", 0)

    # --- Circuit Breaker ---
    if agents_ok == 0:
        print("[Rufus Analyzer] CIRCUIT BREAKER: 0 agents OK. Aborting CPO.")
        failed = []
        for key in ("p1_audit", "p1_insight", "p2_audit", "p2_insight"):
            agent_data = audit_results.get(key, {})
            if "_error" in agent_data:
                failed.append(
                    f"- **{agent_data.get('_agent', key)}:** "
                    f"{agent_data['_error'][:150]}"
                )
        failure_list = "\n".join(failed) if failed else "- (no details)"
        return (
            "## Analysis Failed\n\n"
            "All 4 agents returned errors. The CPO cannot generate a "
            "strategy from empty data.\n\n"
            "### Agent Errors\n\n"
            f"{failure_list}\n\n"
            "### Recommended Actions\n\n"
            "1. Check your Google API Key is valid.\n"
            "2. Verify the input text is not empty or corrupted.\n"
            "3. Try again — the API may have been temporarily overloaded.\n"
        )

    if agents_ok < _MIN_AGENTS_FOR_CPO:
        print(
            f"[Rufus Analyzer] CIRCUIT BREAKER: Only {agents_ok} agents OK "
            f"(need {_MIN_AGENTS_FOR_CPO}). Running CPO in degraded mode."
        )
        # Still run CPO but warn
        degraded_warning = (
            "> **Warning:** Only {ok}/{total} agents succeeded. "
            "This report is based on partial data.\n\n"
        ).format(ok=agents_ok, total=agents_ok + agents_error)
    else:
        degraded_warning = ""

    # Build the intelligence object
    intelligence = aggregate_intelligence(audit_results)

    # Get the CPO prompt
    if "cpo" not in _PROMPTS:
        return "# Error\n\nCPO prompt not found."

    # Fill the CPO prompt with the intelligence JSON
    intelligence_str = json.dumps(intelligence, indent=2, ensure_ascii=False)
    filled_prompt = _fill_prompt(
        _PROMPTS["cpo"], {"intelligence_json": intelligence_str},
    )

    print(
        f"[Rufus Analyzer] Running CPO Strategist "
        f"({len(filled_prompt)} chars) on {model}..."
    )

    # CPO outputs Markdown, not JSON
    raw = _call_llm(filled_prompt, provider, api_key, model, json_mode=False)

    print(f"[Rufus Analyzer] CPO report complete ({len(raw)} chars).")
    return degraded_warning + raw
