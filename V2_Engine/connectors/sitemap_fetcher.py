"""
Sitemap Fetcher — Recursive XML sitemap crawler.

Handles both simple sitemaps and nested <sitemapindex> structures.
Returns a flat list of URL dicts ready for classification.
"""

import requests
import xml.etree.ElementTree as ET


# Common XML namespace used by sitemaps
_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

# Reasonable limits
_MAX_DEPTH = 5
_TIMEOUT = 15  # seconds per request


def fetch_all_urls(sitemap_url: str, *, _depth: int = 0) -> list[dict]:
    """
    Recursively fetch all <url> entries from a sitemap.

    If the document is a <sitemapindex> (contains child <sitemap> elements),
    each child sitemap is fetched recursively until actual <url> entries are found.

    Returns:
        List of dicts: [{'url': '...', 'lastmod': '...'}, ...]
        lastmod will be an empty string if the tag is absent.
    """
    if _depth > _MAX_DEPTH:
        print(f"  [WARN] Max recursion depth ({_MAX_DEPTH}) reached at {sitemap_url}")
        return []

    try:
        resp = requests.get(sitemap_url, timeout=_TIMEOUT, headers={
            "User-Agent": "OmniTrafficBot/2.0 (+https://anergyacademy.com)"
        })
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  [ERROR] Failed to fetch {sitemap_url}: {e}")
        return []

    try:
        root = ET.fromstring(resp.content)
    except ET.ParseError as e:
        print(f"  [ERROR] Failed to parse XML from {sitemap_url}: {e}")
        return []

    # Detect if this is a sitemap index (contains <sitemap> children)
    child_sitemaps = root.findall("sm:sitemap", _NS)
    if child_sitemaps:
        indent = "  " * (_depth + 1)
        print(f"{indent}Found sitemapindex with {len(child_sitemaps)} child sitemaps")
        all_urls = []
        for child in child_sitemaps:
            loc = child.find("sm:loc", _NS)
            if loc is not None and loc.text:
                child_url = loc.text.strip()
                print(f"{indent}-> Fetching: {child_url}")
                all_urls.extend(fetch_all_urls(child_url, _depth=_depth + 1))
        return all_urls

    # Otherwise, extract <url> entries directly
    url_entries = root.findall("sm:url", _NS)
    results = []
    for entry in url_entries:
        loc = entry.find("sm:loc", _NS)
        lastmod = entry.find("sm:lastmod", _NS)
        if loc is not None and loc.text:
            results.append({
                "url": loc.text.strip(),
                "lastmod": lastmod.text.strip() if lastmod is not None and lastmod.text else "",
            })

    return results
