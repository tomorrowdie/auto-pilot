"""
Test Runner — Validates the MarketAnalyzer against real data.

Usage:
    python -m V2_Engine.processors.source_0_market_data.test_analysis
    (run from the project root: 008-Auto-Pilot/)
"""

import json
import os
import sys

import pandas as pd

# Ensure project root is on the path
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from V2_Engine.processors.source_0_market_data.analyzer import MarketAnalyzer
from V2_Engine.config import V2_DATABASE_DIR


INPUT_FILE = os.path.join(V2_DATABASE_DIR, "debug_source0_h10.csv")


def main():
    print("=" * 60)
    print("  Source 0 — Market Analyzer Test Run")
    print("=" * 60)

    # --- Step 1: Load the cleaned CSV from Phase 1 ---
    print(f"\n[1/3] Loading data from:\n      {INPUT_FILE}")

    if not os.path.exists(INPUT_FILE):
        print("  [FAIL] File not found. Run test_ingest.py first.")
        return

    df = pd.read_csv(INPUT_FILE)
    print(f"      Loaded {len(df)} rows x {len(df.columns)} cols")

    # --- Step 2: Run the analyzer ---
    print(f"\n[2/3] Running MarketAnalyzer.analyze() ...")
    analyzer = MarketAnalyzer()
    snapshot = analyzer.analyze(df)

    # --- Step 3: Print the result as JSON ---
    print(f"\n[3/3] Market Snapshot (JSON):\n")

    # Custom serializer for non-JSON-serializable types (NaN, inf, etc.)
    def _safe_json(obj):
        if isinstance(obj, float):
            if obj != obj:       # NaN
                return None
            if obj == float("inf") or obj == float("-inf"):
                return None
        return obj

    # Walk the dict and sanitize
    def _sanitize(d):
        if isinstance(d, dict):
            return {k: _sanitize(v) for k, v in d.items()}
        if isinstance(d, list):
            return [_sanitize(v) for v in d]
        return _safe_json(d)

    clean_snapshot = _sanitize(snapshot)
    print(json.dumps(clean_snapshot, indent=2))

    # --- Assertions for Phase 4 ---
    assert "sellers" in snapshot, "Missing 'sellers' key in snapshot"
    assert "brands" in snapshot, "Missing 'brands' key in snapshot"

    brands = snapshot["brands"]
    if "error" not in brands:
        assert "hhi" in brands, "Missing 'hhi' in brands section"
        print(f"\n  [BRANDS] HHI Score: {brands['hhi']['score']} — {brands['hhi']['classification']}")
        print(f"           {brands['hhi']['interpretation']}")
        print(f"           Total brands: {brands['total_brands']}")
    else:
        print(f"\n  [BRANDS] Skipped (no brand column): {brands['error']}")

    sellers = snapshot["sellers"]
    print(f"  [SELLERS] Total sellers: {sellers.get('total_sellers', 'N/A')}")
    print(f"            Country distribution: {len(sellers.get('country_distribution', {}))} countries")

    print("\n" + "=" * 60)
    print("  DONE. MarketAnalyzer is operational (Phase 4 verified).")
    print("=" * 60)


if __name__ == "__main__":
    main()
