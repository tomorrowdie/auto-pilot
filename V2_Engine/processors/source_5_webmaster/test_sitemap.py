"""
Test Runner — Fetches a live sitemap, classifies URLs, and saves the inventory.

Usage:
    python -m V2_Engine.processors.source_5_webmaster.test_sitemap
    (run from the project root: 008-Auto-Pilot/)
"""

import os
import sys

# Ensure project root is on the path so imports resolve cleanly
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from V2_Engine.connectors.sitemap_fetcher import fetch_all_urls
from V2_Engine.processors.source_5_webmaster.link_classifier import classify_urls
from V2_Engine.config import V2_DATABASE_DIR


TARGET_SITEMAP = "https://anergyacademy.com/sitemap.xml"
OUTPUT_FILE = os.path.join(V2_DATABASE_DIR, "internal_links_v1.csv")


def main():
    print("=" * 60)
    print("  Source 5 — Sitemap Scanner Test Run")
    print("=" * 60)
    print(f"\n  Target: {TARGET_SITEMAP}\n")

    # --- Step 1: Fetch ---
    print("[1/3] Fetching sitemap (recursive)...")
    raw_urls = fetch_all_urls(TARGET_SITEMAP)
    print(f"      Found {len(raw_urls)} URLs total.\n")

    if not raw_urls:
        print("[FAIL] No URLs fetched. Check the sitemap URL or network.")
        return

    # --- Step 2: Classify ---
    print("[2/3] Classifying URLs...")
    df = classify_urls(raw_urls)

    type_counts = df["type"].value_counts()
    print("\n      Type Breakdown:")
    for page_type, count in type_counts.items():
        print(f"        {page_type:12s} -> {count:>4d} URLs")
    print()

    # --- Step 3: Save ---
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")
    print(f"[3/3] Saved Link Inventory to:\n      {OUTPUT_FILE}")

    # Show a sample
    print("\n--- Sample (first 10 rows) ---")
    print(df.head(10).to_string(index=False))
    print("\n" + "=" * 60)
    print("  DONE. Link Inventory ready for Source 6 (SEO Writer).")
    print("=" * 60)


if __name__ == "__main__":
    main()
