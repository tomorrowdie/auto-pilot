"""
Link Classifier — Categorises URLs by page type using path heuristics.

Designed for Shopify stores but works with any site that uses
conventional URL patterns (/products/, /collections/, /blogs/, etc.).
"""

import re
from urllib.parse import urlparse

import pandas as pd


# Each rule is checked in order; first match wins.
_RULES: list[tuple[str, re.Pattern]] = [
    ("PRODUCT",    re.compile(r"/products/", re.IGNORECASE)),
    ("COLLECTION", re.compile(r"/collections/", re.IGNORECASE)),
    ("BLOG",       re.compile(r"/blogs?/|/news/|/articles?/|/journal/", re.IGNORECASE)),
]


def _classify_single(url: str) -> str:
    """Return the page type for a single URL."""
    path = urlparse(url).path
    for label, pattern in _RULES:
        if pattern.search(path):
            return label
    return "PAGE"


def classify_urls(url_list: list[dict]) -> pd.DataFrame:
    """
    Classify a list of URL dicts into a typed DataFrame.

    Args:
        url_list: Output of fetch_all_urls() —
                  [{'url': '...', 'lastmod': '...'}, ...]

    Returns:
        DataFrame with columns: [url, type, lastmod]
    """
    rows = []
    for entry in url_list:
        rows.append({
            "url": entry["url"],
            "type": _classify_single(entry["url"]),
            "lastmod": entry.get("lastmod", ""),
        })

    df = pd.DataFrame(rows, columns=["url", "type", "lastmod"])
    return df
