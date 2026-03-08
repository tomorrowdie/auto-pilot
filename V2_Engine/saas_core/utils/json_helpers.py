"""
Shared JSON repair utility for LLM-generated output.

LLM responses routinely fail strict json.loads() due to:
  - Markdown fences (```json ... ```)
  - Trailing commas before } or ]
  - Preamble / postamble text surrounding the JSON block
  - Missing outer braces (partial JSON objects)
  - Boolean/null tokens in wrong case (true/false/null vs True/False/None)
  - Truncated output when max_tokens is reached mid-JSON

This module provides a single function `parse_llm_json` that runs a
7-stage repair pipeline and never raises — it always returns a dict.

Usage:
    from V2_Engine.saas_core.utils.json_helpers import parse_llm_json

    result = parse_llm_json(llm_raw_text)
    result = parse_llm_json(llm_raw_text, fallback={"key": []})
"""

from __future__ import annotations

import ast
import json
import re


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_llm_json(raw_text: str, fallback: dict | None = None) -> dict:
    """
    7-stage robust JSON parser for LLM output. Never raises.

    Stages:
      1. Strip markdown fences (```json … ```)
      2. Extract outermost { } or [ ] block (removes preamble/postamble text)
      3. Fix trailing commas before } or ]
      4. json.loads — standard parse
      5. json.loads with outer brace wrap (catches missing outer {})
      6. ast.literal_eval with JSON→Python token substitution
      7. Truncation repair — close open strings + brackets, retry json.loads
      8. Return fallback (caller-provided or empty dict)

    Args:
        raw_text: Raw string from the LLM response.
        fallback: Dict to return if all stages fail. Defaults to {}.

    Returns:
        Parsed dict. If the root JSON is an array it is wrapped as
        {"items": [...]}. Never raises.
    """
    _fallback = fallback if fallback is not None else {}

    if not raw_text or not raw_text.strip():
        return _fallback

    cleaned = raw_text.strip()

    # ── Stage 1: Strip markdown fences ───────────────────────────────────
    cleaned = re.sub(r"^```json\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^```\s*",     "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"```\s*$",     "", cleaned)
    cleaned = cleaned.strip()

    # ── Stage 2: Extract outermost { } or [ ] block ───────────────────────
    cleaned = _extract_json_block(cleaned)

    # ── Stage 3: Fix trailing commas ─────────────────────────────────────
    fixed = re.sub(r",\s*([}\]])", r"\1", cleaned)

    # ── Stages 4 + 5: json.loads (direct + brace-wrapped) ────────────────
    for text in (fixed, cleaned):
        result = _try_loads(text)
        if result is not None:
            return result

    for text in (fixed, cleaned):
        result = _try_loads("{" + text + "}")
        if result is not None:
            return result

    # ── Stage 6: ast.literal_eval with JSON → Python token substitution ──
    for text in (fixed, cleaned):
        result = _try_ast(text)
        if result is not None:
            return result
        result = _try_ast("{" + text + "}")
        if result is not None:
            return result

    # ── Stage 7: Truncation repair ────────────────────────────────────────
    repaired = _close_truncated(fixed)
    if repaired != fixed:
        result = _try_loads(repaired)
        if result is not None:
            return result

    # ── Stage 8: Fallback ─────────────────────────────────────────────────
    _log(
        f"parse_llm_json: all stages failed "
        f"({len(cleaned)} chars). Returning fallback."
    )
    return _fallback


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _extract_json_block(text: str) -> str:
    """
    Return the substring from the first { or [ to the matching last } or ].

    If neither is found, return the text unchanged.
    """
    first_brace   = text.find("{")
    first_bracket = text.find("[")

    if first_brace == -1 and first_bracket == -1:
        return text

    if first_brace == -1:
        start_idx, end_char = first_bracket, "]"
    elif first_bracket == -1:
        start_idx, end_char = first_brace, "}"
    elif first_brace <= first_bracket:
        start_idx, end_char = first_brace, "}"
    else:
        start_idx, end_char = first_bracket, "]"

    last_idx = text.rfind(end_char)
    if last_idx > start_idx:
        return text[start_idx : last_idx + 1]
    return text


def _try_loads(text: str) -> dict | None:
    """Try json.loads; return dict/wrapped-list on success, None on failure."""
    try:
        result = json.loads(text)
        if isinstance(result, list):
            return {"items": result}
        if isinstance(result, dict):
            return result
    except (json.JSONDecodeError, ValueError):
        pass
    return None


def _try_ast(text: str) -> dict | None:
    """Try ast.literal_eval after JSON → Python token substitution."""
    pythonized = re.sub(r"\btrue\b",  "True",  text)
    pythonized = re.sub(r"\bfalse\b", "False", pythonized)
    pythonized = re.sub(r"\bnull\b",  "None",  pythonized)
    try:
        result = ast.literal_eval(pythonized)
        if isinstance(result, dict):
            return result
        if isinstance(result, list):
            return {"items": result}
    except (ValueError, SyntaxError):
        pass
    return None


def _close_truncated(text: str) -> str:
    """
    Close a truncated JSON string by scanning for open strings/brackets.

    Tracks:
      - Whether we are inside a string literal (and handles backslash escapes)
      - A stack of expected closing characters (} or ])

    Appends the necessary closing characters in LIFO order.
    """
    stack: list[str] = []
    in_string   = False
    escape_next = False

    for ch in text:
        if escape_next:
            escape_next = False
            continue
        if ch == "\\" and in_string:
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            stack.append("}")
        elif ch == "[":
            stack.append("]")
        elif ch in ("}",  "]") and stack:
            stack.pop()

    # Close any unterminated string first, then all open containers
    suffix = '"' if in_string else ""
    suffix += "".join(reversed(stack))
    return text + suffix


def _log(msg: str) -> None:
    print(f"[json_helpers] {msg}")
