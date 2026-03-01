"""
Cerebro Dashboard — Source 1 Traffic Analysis UI.

Renders the Helium 10 Cerebro "copycat" interface:
    - Strategy Selector (preset volume buckets)
    - Advanced Filter Deck (collapsible)
    - Action Bar (counter + export tools)
    - AgGrid Data Grid (pagination, checkboxes, sorting)
"""

import os
from datetime import datetime

import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

from V2_Engine.processors.source_1_traffic.cerebro_filters import (
    apply_cerebro_filters,
    get_strategy_preset,
)
from V2_Engine.processors.source_1_traffic.cerebro_ingestor import (
    ingest_cerebro_data,
)
from V2_Engine.knowledge_base.manager import KnowledgeManager

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
_RAW_DIR = os.path.join(_PROJECT_ROOT, "data", "raw", "source_1_market")
_PARQUET_FILE = os.path.join(
    _PROJECT_ROOT, "data", "processed", "source_1_cerebro.parquet"
)

# Display column names (snake_case -> Original H10 Headers)
_DISPLAY_NAMES = {
    "keyword_phrase": "Keyword Phrase",
    "aba_total_click_share": "ABA Total Click Share",
    "aba_total_conv_share": "ABA Total Conv. Share",
    "keyword_sales": "Keyword Sales",
    "cerebro_iq_score": "Cerebro IQ Score",
    "search_volume": "Search Volume",
    "search_volume_trend": "Search Volume Trend",
    "h10_ppc_sugg_bid": "H10 PPC Sugg. Bid",
    "h10_ppc_sugg_min_bid": "H10 PPC Sugg. Min Bid",
    "h10_ppc_sugg_max_bid": "H10 PPC Sugg. Max Bid",
    "sponsored_asins": "Sponsored ASINs",
    "competing_products": "Competing Products",
    "cpr": "CPR",
    "organic": "Organic",
    "title_density": "Title Density",
    "smart_complete": "Smart Complete",
    "amazon_recommended": "Amazon Recommended",
    "word_count": "Word Count",
}

_KB_FOLDER = "1_keyword_traffic"


# ---------------------------------------------------------------------------
# Strategy callback
# ---------------------------------------------------------------------------
def _on_strategy_change():
    """Update volume filters when strategy preset changes."""
    p = get_strategy_preset(st.session_state["cerebro_strategy"])
    st.session_state["c_vol_min"] = p.get("search_volume_min", 0)
    st.session_state["c_vol_max"] = p.get("search_volume_max", 0)


# ---------------------------------------------------------------------------
# Main render function
# ---------------------------------------------------------------------------
def render_cerebro_page():
    """Render the Source 1 Cerebro dashboard."""

    st.header("Traffic Cerebro")
    st.caption("Keyword Intelligence \u2014 Source 1")

    # --- Upload Source 1 Data ---
    with st.expander("\U0001f4c2 Upload Source 1 Data (Cerebro CSV)", expanded=False):
        uploaded_csv = st.file_uploader(
            "Choose a CSV file", type=["csv"], key="cerebro_upload",
        )
        if uploaded_csv is not None:
            os.makedirs(_RAW_DIR, exist_ok=True)
            save_path = os.path.join(_RAW_DIR, uploaded_csv.name)
            with open(save_path, "wb") as f:
                f.write(uploaded_csv.getbuffer())
            with st.spinner("Processing Cerebro CSV..."):
                ingest_cerebro_data(csv_path=save_path)
            st.session_state["cerebro_df"] = pd.read_parquet(_PARQUET_FILE)
            st.success(f"Ingested: {uploaded_csv.name}")

    # --- Load Data (fallback to existing Parquet) ---
    if "cerebro_df" not in st.session_state:
        if not os.path.exists(_PARQUET_FILE):
            st.warning(
                "No processed data found. Upload a Cerebro CSV above, "
                "or run:\n\n"
                "`python -m V2_Engine.processors.source_1_traffic.cerebro_ingestor`"
            )
            return
        st.session_state["cerebro_df"] = pd.read_parquet(_PARQUET_FILE)

    df_full = st.session_state["cerebro_df"]
    total_keywords = len(df_full)

    # --- Initialize volume defaults (Level 1) ---
    if "c_vol_min" not in st.session_state:
        st.session_state["c_vol_min"] = 0
    if "c_vol_max" not in st.session_state:
        st.session_state["c_vol_max"] = 8000

    # ===================================================================
    # STRATEGY SELECTOR
    # ===================================================================
    strategy = st.selectbox(
        "Strategy Preset",
        options=["Level 1", "Level 2", "Level 3", "Level 4", "Custom"],
        key="cerebro_strategy",
        on_change=_on_strategy_change,
        help="Level 1: \u22648K | Level 2: 8\u201310K | Level 3: 10\u201320K | Level 4: 20K+",
    )

    # ===================================================================
    # FILTER DECK
    # ===================================================================
    with st.expander("Advanced Filters", expanded=False):
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**Volume & Sales**")
            vol_min = st.number_input(
                "Search Volume Min", min_value=0, key="c_vol_min",
                help="0 = no minimum",
            )
            vol_max = st.number_input(
                "Search Volume Max", min_value=0, key="c_vol_max",
                help="0 = no maximum",
            )
            sales_min = st.number_input(
                "Keyword Sales Min", min_value=0, value=0, key="c_sales_min",
            )
            sales_max = st.number_input(
                "Keyword Sales Max", min_value=0, value=0, key="c_sales_max",
            )
            wc_min = st.number_input(
                "Word Count Min", min_value=0, value=0, key="c_wc_min",
            )
            wc_max = st.number_input(
                "Word Count Max", min_value=0, value=0, key="c_wc_max",
            )

        with col2:
            st.markdown("**Competition**")
            comp_min = st.number_input(
                "Competing Products Min", min_value=0, value=0, key="c_comp_min",
            )
            comp_max = st.number_input(
                "Competing Products Max", min_value=0, value=0, key="c_comp_max",
            )
            td_min = st.number_input(
                "Title Density Min", min_value=0, value=0, key="c_td_min",
            )
            td_max = st.number_input(
                "Title Density Max", min_value=0, value=0, key="c_td_max",
            )
            iq_min = st.number_input(
                "Cerebro IQ Score Min", min_value=0, value=0, key="c_iq_min",
            )
            iq_max = st.number_input(
                "Cerebro IQ Score Max", min_value=0, value=0, key="c_iq_max",
            )

        with col3:
            st.markdown("**Trends & Shares**")
            trend_min = st.number_input(
                "SV Trend % Min", min_value=-999, value=0, key="c_trend_min",
                help="Whole number, e.g. -50",
            )
            trend_max = st.number_input(
                "SV Trend % Max", min_value=-999, value=0, key="c_trend_max",
            )
            aba_click_min = st.number_input(
                "ABA Click Share Min", min_value=0.0, value=0.0,
                key="c_aba_click_min",
            )
            aba_click_max = st.number_input(
                "ABA Click Share Max", min_value=0.0, value=0.0,
                key="c_aba_click_max",
            )
            aba_conv_min = st.number_input(
                "ABA Conv Share Min", min_value=0.0, value=0.0,
                key="c_aba_conv_min",
            )
            aba_conv_max = st.number_input(
                "ABA Conv Share Max", min_value=0.0, value=0.0,
                key="c_aba_conv_max",
            )
            st.markdown("**Match Type**")
            match_types = st.multiselect(
                "Match Types",
                options=["Organic", "Sponsored", "Smart Complete"],
                default=[],
                key="c_match_types",
            )

        # Text filters (full width)
        tcol1, tcol2 = st.columns(2)
        with tcol1:
            phrases_in = st.text_input(
                "Phrases Containing", key="c_phrases_in",
                help="Comma separated. All terms must match.",
            )
        with tcol2:
            phrases_out = st.text_input(
                "Exclude Phrases", key="c_phrases_out",
                help="Comma separated. None may appear.",
            )

    # ===================================================================
    # BUILD FILTER DICT
    # ===================================================================
    filters = {}

    if vol_min > 0:
        filters["search_volume_min"] = vol_min
    if vol_max > 0:
        filters["search_volume_max"] = vol_max
    if sales_min > 0:
        filters["sales_min"] = sales_min
    if sales_max > 0:
        filters["sales_max"] = sales_max
    if wc_min > 0:
        filters["word_count_min"] = wc_min
    if wc_max > 0:
        filters["word_count_max"] = wc_max
    if comp_min > 0:
        filters["competing_products_min"] = comp_min
    if comp_max > 0:
        filters["competing_products_max"] = comp_max
    if td_min > 0:
        filters["title_density_min"] = td_min
    if td_max > 0:
        filters["title_density_max"] = td_max
    if iq_min > 0:
        filters["cerebro_iq_score_min"] = iq_min
    if iq_max > 0:
        filters["cerebro_iq_score_max"] = iq_max
    if trend_min != 0:
        filters["search_volume_trend_min"] = trend_min
    if trend_max != 0:
        filters["search_volume_trend_max"] = trend_max
    if aba_click_min > 0:
        filters["aba_click_share_min"] = aba_click_min
    if aba_click_max > 0:
        filters["aba_click_share_max"] = aba_click_max
    if aba_conv_min > 0:
        filters["aba_conv_share_min"] = aba_conv_min
    if aba_conv_max > 0:
        filters["aba_conv_share_max"] = aba_conv_max
    if match_types:
        filters["match_types"] = match_types
    if phrases_in:
        filters["phrases_containing"] = phrases_in
    if phrases_out:
        filters["exclude_phrases"] = phrases_out

    # ===================================================================
    # APPLY FILTERS
    # ===================================================================
    filtered_df = apply_cerebro_filters(df_full, filters)
    filtered_count = len(filtered_df)

    # ===================================================================
    # ACTION BAR
    # ===================================================================
    st.divider()
    bar1, bar2 = st.columns([3, 1])

    with bar1:
        st.markdown(
            f"**Showing {filtered_count:,} of {total_keywords:,} Keywords**"
        )

    with bar2:
        csv_bytes = filtered_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "\u2b07 Export CSV",
            data=csv_bytes,
            file_name="cerebro_filtered.csv",
            mime="text/csv",
            key="c_csv_download",
            use_container_width=True,
        )

    # --- Twin-File KB Save ---
    with st.expander("Save to Knowledge Base (Twin-File)", expanded=False):
        kb_col1, kb_col2 = st.columns([3, 1])
        with kb_col1:
            project_name = st.text_input(
                "Project Name", key="c_project_name",
                placeholder="e.g. Baby Teether Strategy",
            )
        with kb_col2:
            save_mode = st.radio(
                "Save Mode", key="c_save_mode",
                options=[
                    "Full Analysis (All Filtered)",
                    "Selected Keywords Only",
                ],
            )

        save_kb = st.button(
            "\U0001f4be Save to KB", type="primary", key="c_save_kb",
            use_container_width=True,
        )

        if save_kb:
            if not project_name.strip():
                st.warning("Enter a project name.")
            else:
                kb = KnowledgeManager()
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                filename = kb.make_filename(project_name.strip())

                if save_mode == "Selected Keywords Only":
                    selected_rows = st.session_state.get(
                        "cerebro_selected_rows", None,
                    )
                    if selected_rows is None or len(selected_rows) == 0:
                        st.warning(
                            "No rows selected. Use the checkboxes in the grid."
                        )
                    else:
                        sel_df = pd.DataFrame(selected_rows)
                        kw_col = "Keyword Phrase"
                        if kw_col not in sel_df.columns:
                            kw_col = "keyword_phrase"
                        keywords = sel_df[kw_col].tolist()

                        md_lines = [
                            f"# {project_name.strip()}",
                            "",
                            f"**Source:** Cerebro Traffic Analysis",
                            f"**Generated:** {now}",
                            f"**Keywords:** {len(keywords):,} selected",
                            f"**Strategy:** {strategy}",
                            "",
                            "## Keyword List",
                            "",
                        ]
                        for kw in keywords:
                            md_lines.append(f"- {kw}")
                        md_lines.append("")

                        md_content = "\n".join(md_lines)
                        csv_df = pd.DataFrame({"keyword_phrase": keywords})
                        kb.save_insight(
                            _KB_FOLDER, filename, md_content,
                            dataframe=csv_df,
                            project_slug=st.session_state.get("project_slug", ""),
                        )
                        csv_name = filename.replace(".md", ".csv")
                        st.success(
                            f"Saved {len(keywords):,} keywords! "
                            f"\u2192 `{_KB_FOLDER}/{filename}` + `{csv_name}`"
                        )
                else:
                    md_lines = [
                        f"# {project_name.strip()}",
                        "",
                        f"**Source:** Cerebro Traffic Analysis",
                        f"**Generated:** {now}",
                        f"**Keywords:** {filtered_count:,} "
                        f"(filtered from {total_keywords:,})",
                        f"**Strategy:** {strategy}",
                        "",
                        "## Filters Applied",
                        "",
                    ]
                    if filters:
                        for k, v in filters.items():
                            md_lines.append(f"- **{k}:** {v}")
                    else:
                        md_lines.append("- None (full dataset)")

                    md_lines += [
                        "",
                        "## Summary Statistics",
                        "",
                        f"- Avg Search Volume: "
                        f"{filtered_df['search_volume'].mean():,.0f}",
                        f"- Avg Keyword Sales: "
                        f"{filtered_df['keyword_sales'].mean():,.0f}",
                        f"- Avg Competing Products: "
                        f"{filtered_df['competing_products'].mean():,.0f}",
                        f"- Avg Cerebro IQ Score: "
                        f"{filtered_df['cerebro_iq_score'].mean():,.0f}",
                        "",
                    ]

                    md_content = "\n".join(md_lines)
                    kb.save_insight(
                        _KB_FOLDER, filename, md_content,
                        dataframe=filtered_df,
                        project_slug=st.session_state.get("project_slug", ""),
                    )
                    csv_name = filename.replace(".md", ".csv")
                    st.success(
                        f"Saved! \u2192 `{_KB_FOLDER}/{filename}` + "
                        f"`{csv_name}`"
                    )

    # ===================================================================
    # DATA GRID (AgGrid)
    # ===================================================================
    st.divider()

    display_df = filtered_df.rename(columns=_DISPLAY_NAMES)

    gb = GridOptionsBuilder.from_dataframe(display_df)
    gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=50)
    gb.configure_selection(
        selection_mode="multiple",
        use_checkbox=True,
        header_checkbox=True,
        groupSelectsChildren=True,
        groupSelectsFiltered=True,
    )
    gb.configure_default_column(sortable=True, resizable=True)
    gb.configure_column("Keyword Phrase", pinned="left", width=250)

    grid_response = AgGrid(
        display_df,
        gridOptions=gb.build(),
        height=600,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        theme="streamlit",
    )

    selected = grid_response.get("selected_rows", None)
    if selected is not None and len(selected) > 0:
        st.session_state["cerebro_selected_rows"] = selected
