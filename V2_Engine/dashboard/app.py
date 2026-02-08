"""
Catalog Insight — V2 Dashboard.

Pure UI layer. All business logic comes from the V2 Engine:
    - H10Ingestor      -> cleans + ranks the uploaded CSV
    - MarketAnalyzer    -> produces the Market Snapshot dict
    - converters        -> transforms snapshots into Markdown (USB Protocol)
    - KnowledgeManager  -> generic Hub that stores Markdown files in folders

Usage:
    streamlit run V2_Engine/dashboard/app.py
    (from 008-Auto-Pilot/)
"""

import os
import sys
import tempfile

import pandas as pd
import requests
import streamlit as st

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from V2_Engine.processors.source_0_market_data.h10_ingestor import H10Ingestor
from V2_Engine.processors.source_0_market_data.analyzer import MarketAnalyzer
from V2_Engine.knowledge_base.manager import KnowledgeManager
from V2_Engine.knowledge_base.converters import snapshot_to_markdown

# Ensure storage directory exists for Cloud Deployment
os.makedirs(
    os.path.join(_PROJECT_ROOT, "V2_Engine", "knowledge_base", "storage"),
    exist_ok=True,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Catalog Insight",
    page_icon="\U0001f50d",
    layout="wide",
    initial_sidebar_state="expanded",
)

kb = KnowledgeManager()

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("Catalog Insight")
    st.caption("Market Intelligence Dashboard")
    st.divider()

    # --- File Upload ---
    uploaded = st.file_uploader(
        "Upload H10 Chrome",
        type=["csv"],
        accept_multiple_files=True,
        help="Upload one or more Helium 10 CSV exports.",
    )

    _CATALOG_FOLDER = "Catalog Insight"

    if uploaded:
        if st.button("Analyze", type="primary", use_container_width=True):
            tmp_paths: list[str] = []
            for f in uploaded:
                tmp = tempfile.NamedTemporaryFile(
                    delete=False, suffix=".csv", prefix="h10_"
                )
                tmp.write(f.getbuffer())
                tmp.close()
                tmp_paths.append(tmp.name)

            with st.spinner("Running V2 Engine..."):
                ingestor = H10Ingestor()
                df = ingestor.ingest(tmp_paths)
                snapshot = MarketAnalyzer().analyze(df)

            st.session_state["df"] = df
            st.session_state["snapshot"] = snapshot
            st.session_state["file_info"] = ingestor.file_info

            for p in tmp_paths:
                try:
                    os.unlink(p)
                except OSError:
                    pass

            # Auto-save results to Catalog Insight/
            from datetime import datetime as _dt
            _ts = _dt.now().strftime("%Y%m%d_%H%M")
            _title = f"catalog_insight_{_ts}"
            _md = snapshot_to_markdown(_title, snapshot)
            _md_fname = kb.make_filename(_title)
            kb.save_insight(_CATALOG_FOLDER, _md_fname, _md)

            # Save cleaned CSV alongside the markdown
            _csv_fname = _md_fname.replace(".md", ".csv")
            _csv_dir = os.path.join(
                _PROJECT_ROOT, "V2_Engine", "knowledge_base",
                "storage", _CATALOG_FOLDER,
            )
            os.makedirs(_csv_dir, exist_ok=True)
            df.to_csv(os.path.join(_csv_dir, _csv_fname), index=False)

            st.success(
                f"Processed {len(df)} rows. "
                f"Saved to `{_CATALOG_FOLDER}/{_md_fname}`"
            )

    if "file_info" in st.session_state:
        st.divider()
        st.subheader("Loaded Files")
        for fi in st.session_state["file_info"]:
            st.text(f"  {fi['filename']}")
            st.text(f"    {fi['rows']} rows, {fi['columns']} cols")

    # --- Test API Connection ---
    st.divider()
    with st.expander("\U0001f50c Test API Connection", expanded=False):
        api_url = st.text_input(
            "API Base URL",
            value="https://auto-pilot-k5zw.onrender.com",
            key="api_base_url",
        )
        if st.button("Get Latest Analysis", key="btn_get_latest", use_container_width=True):
            endpoint = f"{api_url.rstrip('/')}/api/v1/knowledge/latest/catalog_insight"
            try:
                resp = requests.get(endpoint, timeout=30)
                if resp.status_code == 200:
                    result = resp.json()
                    st.success(f"Connected! Latest: **{result.get('filename', '?')}**")
                    st.json(result)
                elif resp.status_code == 404:
                    st.warning("No analyses found yet. Upload a CSV and run Analyze first.")
                else:
                    st.error(f"API returned {resp.status_code}")
                    st.text(resp.text[:500])
            except requests.ConnectionError:
                st.error("Cannot connect to API. Is the server running?")
            except Exception as e:
                st.error(f"Request failed: {e}")

    # --- Knowledge Notebook ---
    st.divider()
    with st.expander("\U0001f9e0 Knowledge Notebook", expanded=True):
        grouped = kb.list_insights()
        if not grouped:
            st.caption("No folders yet. Create one below.")
        else:
            for category, files in grouped.items():
                file_count = len(files)
                label = f"\U0001f4c2 {category} ({file_count})" if file_count else f"\U0001f4c2 {category} (empty)"
                with st.expander(label, expanded=False):
                    if not files:
                        st.caption("No files in this folder.")
                    for item in files:
                        fname = item["filename"]
                        col_view, col_del = st.columns([4, 1])
                        with col_view:
                            if st.button(
                                f"\U0001f4c4 {fname}",
                                key=f"view_{category}_{fname}",
                                use_container_width=True,
                            ):
                                st.session_state["kb_view"] = {
                                    "category": category,
                                    "filename": fname,
                                }
                        with col_del:
                            if st.button(
                                "\U0001f5d1\ufe0f",
                                key=f"del_{category}_{fname}",
                                help=f"Delete {fname}",
                            ):
                                kb.delete_insight(category, fname)
                                viewed = st.session_state.get("kb_view", {})
                                if (
                                    viewed.get("category") == category
                                    and viewed.get("filename") == fname
                                ):
                                    st.session_state.pop("kb_view", None)
                                st.rerun()

        # --- Manage Folders ---
        with st.expander("\u2699\ufe0f Manage Folders", expanded=False):
            # Create new folder
            new_folder = st.text_input(
                "New folder name",
                placeholder="e.g. 1_traffic",
                key="new_folder_input",
            )
            if st.button("Create Folder", key="btn_create_folder"):
                if new_folder.strip():
                    if kb.create_category(new_folder.strip()):
                        st.success(f"Created folder: {new_folder.strip()}")
                        st.rerun()
                    else:
                        st.warning("Folder already exists or invalid name.")
                else:
                    st.warning("Enter a folder name.")

            # Rename folder
            categories = kb.list_categories()
            if categories:
                st.divider()
                rename_from = st.selectbox(
                    "Rename folder",
                    options=categories,
                    key="rename_from_select",
                )
                rename_to = st.text_input(
                    "New name",
                    placeholder="Enter new name",
                    key="rename_to_input",
                )
                if st.button("Rename", key="btn_rename_folder"):
                    if rename_to.strip():
                        if kb.rename_category(rename_from, rename_to.strip()):
                            st.success(f"Renamed: {rename_from} -> {rename_to.strip()}")
                            st.rerun()
                        else:
                            st.warning("Target name already exists or invalid.")
                    else:
                        st.warning("Enter a new name.")

# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------
if "snapshot" not in st.session_state:
    st.header("Catalog Insight")
    st.info("Upload a CSV in the sidebar and click **Analyze** to begin.")
    st.stop()

snapshot: dict = st.session_state["snapshot"]
df: pd.DataFrame = st.session_state["df"]

# ===================================================================
# SAVE TO NOTEBOOK — action bar
# ===================================================================
with st.container():
    save_col1, save_col2, save_col3 = st.columns([2, 2, 1])

    # Dynamic folder list for the dropdown
    categories = kb.list_categories()
    if not categories:
        # Auto-create default folder
        kb.create_category("0_catalog_insight")
        categories = kb.list_categories()

    with save_col1:
        save_title = st.text_input(
            "Insight title",
            value="",
            placeholder="e.g. Garlic Press Market Q1",
            label_visibility="collapsed",
        )
    with save_col2:
        save_folder = st.selectbox(
            "Select Folder",
            options=categories,
            label_visibility="collapsed",
        )
    with save_col3:
        save_clicked = st.button(
            "\U0001f4be Save",
            type="primary",
            use_container_width=True,
        )

    if save_clicked:
        if not save_title.strip():
            st.warning("Please enter a title for this insight.")
        else:
            # USB Protocol: convert snapshot -> Markdown -> save to Hub
            md_content = snapshot_to_markdown(save_title.strip(), snapshot)
            filename = kb.make_filename(save_title.strip())
            kb.save_insight(save_folder, filename, md_content)
            st.success(
                f"Saved to Knowledge Base! \u2192 `{save_folder}/{filename}`"
            )

# ===================================================================
# KNOWLEDGE VIEWER — show selected file from sidebar
# ===================================================================
if "kb_view" in st.session_state:
    _kv = st.session_state["kb_view"]
    with st.expander(
        f"\U0001f4d6 {_kv['category']} / {_kv['filename']}", expanded=True
    ):
        try:
            _content = kb.get_insight(_kv["category"], _kv["filename"])
            st.markdown(_content)
        except FileNotFoundError:
            st.error("File not found \u2014 it may have been deleted.")
        if st.button("Close viewer"):
            st.session_state.pop("kb_view", None)
            st.rerun()

# ===================================================================
# TOP-LEVEL METRICS
# ===================================================================
st.header("Market Snapshot")

col_health, col_pricing, col_perf = st.columns(3)

# --- Column 1: Market Health ---
with col_health:
    st.subheader("Market Health")

    sales_totals = snapshot.get("sales", {}).get("totals", {})
    brands_data = snapshot.get("brands", {})
    sellers_data = snapshot.get("sellers", {})

    revenue_val = None
    for key in ["ASIN Revenue", "Parent Level Revenue", "Revenue"]:
        if key in sales_totals:
            revenue_val = sales_totals[key]
            break

    volume_val = sales_totals.get("Keyword Sales") or sales_totals.get("total_products")

    st.metric("Total Products", f"{sales_totals.get('total_products', 0):,}")

    if revenue_val is not None:
        st.metric("Avg Revenue", f"${revenue_val:,.2f}")
    if volume_val is not None:
        st.metric("Market Volume", f"{volume_val:,.0f}")

    hhi = brands_data.get("hhi", {})
    hhi_score = hhi.get("score")
    if hhi_score is not None:
        if hhi_score < 1500:
            hhi_color = "\U0001f7e2"
        elif hhi_score < 2500:
            hhi_color = "\U0001f7e1"
        else:
            hhi_color = "\U0001f534"
        st.metric("HHI Concentration", f"{hhi_color} {hhi_score:,.0f}")
        st.caption(hhi.get("classification", ""))

    total_brands = brands_data.get("total_brands")
    if total_brands is not None:
        st.metric("Total Brands", f"{total_brands:,}")

# --- Column 2: Pricing ---
with col_pricing:
    st.subheader("Pricing")

    pricing_data = snapshot.get("pricing", {})
    pricing_totals = pricing_data.get("totals", {})

    if "error" in pricing_data:
        st.warning("No pricing data available.")
        st.caption(pricing_data["error"])
    else:
        avg_price = pricing_totals.get("avg_price", 0)
        avg_fee = pricing_totals.get("avg_fee", 0)
        avg_profit = pricing_totals.get("avg_profit", 0)

        st.metric("Avg Price", f"${avg_price:,.2f}")
        st.metric("Avg Fees", f"${avg_fee:,.2f}")
        st.metric("Avg Profit", f"${avg_profit:,.2f}")
        st.metric("Median Price", f"${pricing_totals.get('median_price', 0):,.2f}")

        price_range = pricing_totals.get("min_price", 0), pricing_totals.get("max_price", 0)
        st.caption(f"Range: ${price_range[0]:,.2f} \u2014 ${price_range[1]:,.2f}")

# --- Column 3: Performance ---
with col_perf:
    st.subheader("Performance")

    perf_data = snapshot.get("performance", {})
    perf_totals = perf_data.get("totals", {})

    if "error" in perf_data:
        st.warning("No performance data available.")
        st.caption(perf_data["error"])
    else:
        avg_bsr = perf_totals.get("avg_bsr")
        avg_rating = perf_totals.get("avg_rating")
        avg_reviews = perf_totals.get("avg_review_count")
        review_vel = perf_totals.get("review_velocity")

        if avg_bsr is not None:
            st.metric("Avg BSR", f"{avg_bsr:,.0f}")
        if avg_rating is not None:
            st.metric("Avg Rating", f"{avg_rating:,.2f}")
        if avg_reviews is not None:
            st.metric("Avg Reviews", f"{avg_reviews:,.0f}")
        if review_vel is not None:
            st.metric("Review Velocity", f"{review_vel:,.1f}/mo")

    seller_age = sellers_data.get("avg_seller_age_months")
    if seller_age is not None:
        st.metric("Avg Seller Age", f"{seller_age:,.0f} months")

    country_dist = sellers_data.get("country_distribution", {})
    if country_dist:
        st.metric("Seller Countries", f"{len(country_dist)}")

st.divider()

# ===================================================================
# DEEP-DIVE TABS
# ===================================================================

tab_sales, tab_brands, tab_raw = st.tabs(
    ["Sales by Rank", "Brands & Competition", "Raw Data"]
)

# --- Tab 1: Sales by Rank ---
with tab_sales:
    st.subheader("Sales & Revenue by Rank Tier")

    sales_data = snapshot.get("sales", {})
    by_rank = sales_data.get("by_rank", {})
    metric_cols = sales_data.get("metrics_columns", [])

    if "error" in sales_data:
        st.error(sales_data["error"])
    elif by_rank:
        rows = []
        for tier, values in by_rank.items():
            row = {"Rank Tier": tier, "Count": values.get("count", 0)}
            for col in metric_cols:
                val = values.get(col)
                row[col] = round(val, 2) if val is not None else "\u2014"
            rows.append(row)

        rank_df = pd.DataFrame(rows)
        st.dataframe(rank_df, use_container_width=True, hide_index=True)

        if metric_cols and len(rows) > 0:
            chart_col = metric_cols[0]
            chart_data = []
            for tier, values in by_rank.items():
                val = values.get(chart_col)
                if val is not None:
                    chart_data.append({"Rank Tier": tier, chart_col: val})
            if chart_data:
                chart_df = pd.DataFrame(chart_data).set_index("Rank Tier")
                st.bar_chart(chart_df)

    pricing_by_rank = pricing_data.get("by_rank", {})
    if pricing_by_rank and "error" not in pricing_data:
        st.subheader("Pricing by Rank Tier")
        price_rows = []
        for tier, values in pricing_by_rank.items():
            if values.get("count", 0) == 0:
                continue
            price_rows.append({
                "Rank Tier": tier,
                "Count": values.get("count", 0),
                "Avg Price": values.get("avg_price", "\u2014"),
                "Avg Fee": values.get("avg_fee", "\u2014"),
                "Avg Profit": values.get("avg_profit", "\u2014"),
                "Std Dev": values.get("std_dev", "\u2014"),
                "P25": values.get("p25", "\u2014"),
                "Median": values.get("p50", "\u2014"),
                "P75": values.get("p75", "\u2014"),
            })
        if price_rows:
            st.dataframe(
                pd.DataFrame(price_rows), use_container_width=True, hide_index=True
            )

# --- Tab 2: Brands & Competition ---
with tab_brands:
    st.subheader("Brand Landscape")

    if "error" in brands_data:
        st.error(brands_data["error"])
    else:
        hhi = brands_data.get("hhi", {})
        hhi_score = hhi.get("score", 0)
        if hhi_score < 1500:
            hhi_color = "green"
        elif hhi_score < 2500:
            hhi_color = "orange"
        else:
            hhi_color = "red"

        col_hhi1, col_hhi2 = st.columns([1, 2])
        with col_hhi1:
            st.metric("HHI Score", f"{hhi_score:,.0f}")
            st.markdown(f"**:{hhi_color}[{hhi.get('classification', '')}]**")
        with col_hhi2:
            st.info(hhi.get("interpretation", ""))

        st.divider()

        top_brands = brands_data.get("top_brands", [])
        if top_brands:
            st.subheader(f"Top {len(top_brands)} Brands")

            brand_rows = []
            for b in top_brands[:10]:
                row = {
                    "Brand": b.get("brand", ""),
                    "Products": b.get("product_count", 0),
                    "Market Share %": b.get("market_share_pct", 0),
                }
                if "avg_price" in b and b["avg_price"] is not None:
                    row["Avg Price"] = f"${b['avg_price']:,.2f}"
                if "avg_rating" in b and b["avg_rating"] is not None:
                    row["Avg Rating"] = b["avg_rating"]
                if "avg_bsr" in b and b["avg_bsr"] is not None:
                    row["Avg BSR"] = f"{b['avg_bsr']:,.0f}"
                if "avg_sales" in b and b["avg_sales"] is not None:
                    row["Avg Sales"] = f"{b['avg_sales']:,.0f}"
                brand_rows.append(row)

            brand_df = pd.DataFrame(brand_rows)
            st.dataframe(brand_df, use_container_width=True, hide_index=True)

            chart_brands = top_brands[:5]
            if chart_brands:
                chart_data = pd.DataFrame({
                    "Brand": [b["brand"] for b in chart_brands],
                    "Market Share %": [
                        b.get("market_share_pct", 0) for b in chart_brands
                    ],
                }).set_index("Brand")
                st.bar_chart(chart_data)

        if country_dist:
            st.divider()
            st.subheader("Seller Country Distribution")
            country_rows = []
            for code, info in country_dist.items():
                country_rows.append({
                    "Country": code,
                    "Sellers": info.get("count", 0),
                    "% of Total": info.get("pct", 0),
                    "Revenue Share %": info.get("revenue_share", 0),
                })
            country_df = pd.DataFrame(country_rows)
            st.dataframe(country_df, use_container_width=True, hide_index=True)

# --- Tab 3: Raw Data ---
with tab_raw:
    st.subheader(f"Full Dataset \u2014 {len(df):,} rows x {len(df.columns)} columns")

    all_cols = list(df.columns)
    selected_cols = st.multiselect(
        "Filter columns",
        options=all_cols,
        default=all_cols[:15],
        help="Select which columns to display.",
    )

    if selected_cols:
        st.dataframe(df[selected_cols], use_container_width=True, height=600)
    else:
        st.dataframe(df, use_container_width=True, height=600)

    csv_export = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download Cleaned CSV",
        data=csv_export,
        file_name="v2_cleaned_export.csv",
        mime="text/csv",
    )
