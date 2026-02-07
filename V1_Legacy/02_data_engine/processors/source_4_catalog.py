import sys
import os
import pandas as pd

# --- DYNAMIC IMPORT SETUP ---
# We need to tell Python where to find your new 'catalog_program' folder
# Update this path to match where you created the folder
CATALOG_LIB_PATH = r"C:\Users\john\PycharmProjects\PythonProject\008-Auto-Pilot\data_sample\data_source_4_amazon_catalog"
sys.path.append(CATALOG_LIB_PATH)

try:
    from catalog_program import cleaner, metrics, benchmark
except ImportError as e:
    print(f"⚠️ Error importing Catalog Program: {e}")
    print("Check if __init__.py exists in the catalog_program folder.")


def process_catalog_data(file_path, focus_asin):
    print(f"   [Source 4] Processing Market Catalog...")

    # 1. Load & Clean
    try:
        raw_df = pd.read_csv(file_path, on_bad_lines='skip')
        df = cleaner.clean_market_data(raw_df)
    except Exception as e:
        print(f"   [Error] Loading Catalog failed: {e}")
        return {}

    # 2. Market Stats
    stats = metrics.calculate_market_stats(df)
    top_competitors = metrics.get_top_competitors(df, top_n=5)

    # 3. SWOT Analysis (Focus ASIN)
    swot = benchmark.MarketBenchmarker().analyze_position(df, focus_asin)

    return {
        "market_stats": stats,
        "top_competitors": top_competitors.to_dict('records'),
        "my_position": swot
    }


def generate_report_section(data):
    if not data: return ""

    stats = data['market_stats']
    swot = data['my_position']

    lines = []
    lines.append("## 📊 Phase 4: Market Architecture (Source 4)")
    lines.append(
        f"> **Market Context:** Volume: {stats.get('total_market_volume', 0):,} units/mo | Avg Price: ${stats.get('avg_price', 0):.2f}\n")

    # SWOT
    lines.append("### 🧭 Strategic Position (SWOT)")
    lines.append(f"**Price Strategy:** `{swot.get('price_status', 'Unknown')}`")
    lines.append(f"**Review Health:** `{swot.get('review_status', 'Unknown')}`")

    if swot.get('opportunities'):
        lines.append("\n**⚡ Opportunities:**")
        for opp in swot['opportunities']:
            lines.append(f"* {opp}")

    # Top Competitors
    lines.append("\n### 🏆 Top 5 Competitors to Attack")
    lines.append("| Brand | ASIN | Price | Sales |")
    lines.append("| :--- | :--- | :--- | :--- |")
    for comp in data['top_competitors']:
        lines.append(
            f"| {comp.get('Brand', '-')} | {comp.get('ASIN', '-')} | ${comp.get('Price US', 0)} | {comp.get('Sales', 0):,} |")

    lines.append("\n")
    return "\n".join(lines)