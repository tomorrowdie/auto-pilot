"""
Reviews Dashboard — Source 2 Review Analysis (Happy/Defect) UI.

Renders the review analysis interface:
    - File Uploader (Sorftime Excel)
    - AI Analysis trigger (Gemini via API Key Vault)
    - Happy DNA tab (Brand DNA cards)
    - Defect Tracker tab (bar chart + table)
    - Raw Data tab
    - KB Save (Twin-File Protocol)
"""

import os
from datetime import datetime

import pandas as pd
import streamlit as st

from V2_Engine.processors.source_2_reviews.reviews_ingestor import (
    ingest_reviews,
    save_parquet,
)
from V2_Engine.processors.source_2_reviews.reviews_analyzer import (
    analyze_reviews,
    flatten_happy_results,
    flatten_buying_factors,
    flatten_defect_results,
)
from V2_Engine.knowledge_base.manager import KnowledgeManager
from V2_Engine.saas_core.auth import auth_manager

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
_PARQUET_FILE = os.path.join(
    _PROJECT_ROOT, "data", "processed", "source_2_reviews.parquet"
)
_RAW_DIR = os.path.join(_PROJECT_ROOT, "data", "raw", "source_2_review")

_KB_FOLDER = "2_review_analysis"


# ---------------------------------------------------------------------------
# Main render function
# ---------------------------------------------------------------------------
def render_reviews_page():
    """Render the Source 2 Reviews Analysis dashboard."""

    st.header("Reviews Analysis")
    st.caption("Brand DNA & Defect Tracker \u2014 Source 2")

    # ===================================================================
    # UPLOAD SECTION
    # ===================================================================
    with st.expander("\U0001f4c2 Upload Source 2 Data (Sorftime Excel)", expanded=False):
        uploaded_file = st.file_uploader(
            "Choose a Sorftime Excel file",
            type=["xlsx"],
            key="review_upload",
        )
        if uploaded_file is not None:
            with st.spinner("Processing Sorftime Excel..."):
                df = ingest_reviews(file_obj=uploaded_file)
                save_parquet(df)
            st.session_state["review_df"] = df
            st.success(
                f"Ingested: {uploaded_file.name} "
                f"({len(df)} reviews, ASIN: {df['asin'].nunique()})"
            )

    # ===================================================================
    # LOAD DATA (fallback to existing Parquet)
    # ===================================================================
    if "review_df" not in st.session_state:
        if not os.path.exists(_PARQUET_FILE):
            st.warning(
                "No processed data found. Upload a Sorftime Excel above, "
                "or run:\n\n"
                "`python -m V2_Engine.processors.source_2_reviews.reviews_ingestor`"
            )
            return
        st.session_state["review_df"] = pd.read_parquet(_PARQUET_FILE)

    df = st.session_state["review_df"]
    total_reviews = len(df)
    asin_list = df["asin"].unique().tolist()
    happy_count = len(df[df["rating"] >= 4])
    defect_count = len(df[df["rating"] <= 3])

    # --- Dataset Summary ---
    st.divider()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Reviews", f"{total_reviews:,}")
    m2.metric("ASINs", f"{len(asin_list)}")
    m3.metric("Happy (4-5\u2605)", f"{happy_count:,}")
    m4.metric("Defect (1-3\u2605)", f"{defect_count:,}")

    # ===================================================================
    # CONTROL CENTER — AI Analysis
    # ===================================================================
    st.divider()

    user_id = st.session_state.get("user_id", "dev_admin")
    rev_provider, rev_model = auth_manager.render_tab_model_selector(
        user_id, tab_key="reviews", label="Analysis Model",
    )
    rev_api_key = auth_manager.get_api_key(user_id, rev_provider)

    if not rev_api_key:
        st.warning(
            "\u26a0\ufe0f No API key stored for the selected provider. "
            "Add one via the **API Keys** sidebar."
        )
    else:
        st.caption(f"Connected: **{rev_provider} \u2014 {rev_model}**")

        if st.button(
            "\u2728 Analyze Reviews with AI",
            type="primary",
            use_container_width=True,
            key="btn_analyze_reviews",
        ):
            rev_config = {"key": rev_api_key, "model": rev_model, "provider": rev_provider}
            with st.spinner(
                "AI is reading reviews... (This may take 15-30s per ASIN)"
            ):
                results = analyze_reviews(df, rev_config)

            # Store in session state so it survives refresh
            st.session_state["review_analysis_results"] = results

            # Flatten and store DataFrames
            happy_df = flatten_happy_results(results["happy_results"])
            buying_df = flatten_buying_factors(results["happy_results"])
            defect_df = flatten_defect_results(results["defect_results"])
            st.session_state["brand_dna_df"] = happy_df
            st.session_state["buying_factors_df"] = buying_df
            st.session_state["defect_tracker_df"] = defect_df

            stats = results["stats"]
            st.success(
                f"Analysis complete! "
                f"Processed {stats['total_reviews']} reviews "
                f"({stats['happy_count']} happy, {stats['defect_count']} defect) "
                f"across {stats['asins_processed']} ASIN(s)."
            )

    # ===================================================================
    # VISUALIZATION TABS
    # ===================================================================
    results = st.session_state.get("review_analysis_results")

    tab_happy, tab_defect, tab_raw = st.tabs([
        "\U0001f7e2 Happy DNA",
        "\U0001f534 Defect Tracker",
        "\U0001f4cb Raw Data",
    ])

    # ----- Tab 1: Happy DNA -----
    with tab_happy:
        if results and results.get("happy_results"):
            happy_df = st.session_state.get("brand_dna_df", pd.DataFrame())

            st.metric("Total Happy Reviews", f"{results['stats']['happy_count']:,}")
            st.divider()

            # --- Buying Factors Bar Chart (aggregate across all ASINs) ---
            buying_df = st.session_state.get("buying_factors_df", pd.DataFrame())
            if not buying_df.empty:
                st.subheader("Top Buying Factors")
                chart_bf = (
                    buying_df.groupby("factor", as_index=False)["count"]
                    .sum()
                    .sort_values("count", ascending=False)
                    .head(10)
                )
                if not chart_bf.empty:
                    st.bar_chart(chart_bf.set_index("factor")["count"])
                st.divider()

            for item in results["happy_results"]:
                if "_error" in item:
                    st.error(
                        f"ASIN {item.get('_asin', '?')}: {item['_error']}"
                    )
                    continue

                asin = item.get("_asin", "")
                dna = item.get("brand_dna", {})
                product = item.get("product_name", "Unknown Product")

                st.subheader(f"{product}")
                st.caption(f"ASIN: {asin} \u2014 {item.get('_review_count', 0)} reviews")

                # Primary Hook — large quote
                hook = dna.get("primary_hook", "")
                if hook:
                    st.markdown(
                        f"> \U0001f4a1 **\"{hook}\"**"
                    )

                # Buying Factors — per ASIN quotes
                factors = dna.get("buying_factors", [])
                if factors:
                    with st.expander(
                        f"Buying Factors ({len(factors)} reasons)", expanded=False
                    ):
                        for f in factors:
                            st.markdown(
                                f"**{f.get('factor', '')}** "
                                f"({f.get('count', 0)} mentions) \u2014 "
                                f"\"{f.get('quote', '')}\""
                            )

                col_intents, col_keywords = st.columns(2)

                # COSMO Intents
                with col_intents:
                    st.markdown("**COSMO Intents**")
                    intents = dna.get("cosmo_intents", [])
                    if intents:
                        for intent in intents:
                            st.markdown(f"- {intent}")
                    else:
                        st.caption("No intents extracted.")

                # Rufus Keywords
                with col_keywords:
                    st.markdown("**Rufus Keywords**")
                    keywords = dna.get("rufus_keywords", [])
                    if keywords:
                        st.markdown(", ".join(
                            f"`{kw}`" for kw in keywords
                        ))
                    else:
                        st.caption("No keywords extracted.")

                # EEAT Stories
                experiences = dna.get("eeat_experiences", [])
                if experiences:
                    with st.expander(
                        f"EEAT Stories ({len(experiences)} quotes)", expanded=False
                    ):
                        for exp in experiences:
                            angle = exp.get("angle", "")
                            quote = exp.get("quote", "")
                            context = exp.get("context", "")
                            st.markdown(
                                f"**[{angle}]** \u2014 \"{quote}\"\n\n"
                                f"*Context: {context}*"
                            )
                            st.divider()

                # Competitor Wins
                wins = dna.get("competitor_wins", [])
                if wins:
                    with st.expander("Competitor Wins", expanded=False):
                        for w in wins:
                            st.markdown(f"- {w}")

                st.divider()
        else:
            st.info(
                "No Happy DNA results yet. "
                "Click **Analyze Reviews with Gemini** above."
            )

    # ----- Tab 2: Defect Tracker -----
    with tab_defect:
        if results and results.get("defect_results"):
            defect_df = st.session_state.get("defect_tracker_df", pd.DataFrame())

            st.metric("Total Defect Reviews", f"{results['stats']['defect_count']:,}")
            st.divider()

            # Check for errors
            error_items = [
                r for r in results["defect_results"] if "_error" in r
            ]
            for item in error_items:
                st.error(
                    f"ASIN {item.get('_asin', '?')}: {item['_error']}"
                )

            if not defect_df.empty:
                # Pareto Bar Chart — Issues by Count
                st.subheader("Top Issues (Pareto)")
                chart_df = (
                    defect_df[defect_df["issue"] != ""]
                    .groupby("issue", as_index=False)["count"]
                    .sum()
                    .sort_values("count", ascending=False)
                    .head(10)
                )
                if not chart_df.empty:
                    st.bar_chart(
                        chart_df.set_index("issue")["count"],
                    )

                # Traffic Layer Breakdown
                layer_df = (
                    defect_df[defect_df["impacted_traffic_layer"] != ""]
                    .groupby("impacted_traffic_layer", as_index=False)["count"]
                    .sum()
                    .sort_values("count", ascending=False)
                )
                if not layer_df.empty:
                    st.subheader("Traffic Layer Impact")
                    st.bar_chart(
                        layer_df.set_index("impacted_traffic_layer")["count"],
                    )

                # Representative Quotes
                quotes_df = defect_df[
                    defect_df["representative_quote"].astype(str).str.strip() != ""
                ]
                if not quotes_df.empty:
                    with st.expander(
                        f"Representative Quotes ({len(quotes_df)} issues)",
                        expanded=False,
                    ):
                        for _, row in quotes_df.iterrows():
                            st.markdown(
                                f"**{row['issue']}** \u2014 "
                                f"\"{row['representative_quote']}\""
                            )

                # Detailed Table
                st.subheader("Defect Detail Table")
                st.dataframe(
                    defect_df,
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.caption("No structured defect data to display.")
        else:
            if defect_count == 0:
                st.info(
                    "No defect reviews in this dataset (all reviews are 4-5 stars)."
                )
            else:
                st.info(
                    "No Defect Tracker results yet. "
                    "Click **Analyze Reviews with Gemini** above."
                )

    # ----- Tab 3: Raw Data -----
    with tab_raw:
        st.subheader(
            f"Full Dataset \u2014 {total_reviews:,} reviews"
        )
        st.dataframe(df, use_container_width=True, height=500)

        csv_bytes = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "\u2b07 Export CSV",
            data=csv_bytes,
            file_name="source_2_reviews.csv",
            mime="text/csv",
            key="r_csv_download",
            use_container_width=True,
        )

    # ===================================================================
    # SAVE TO KNOWLEDGE BASE (Unified Report — Twin-File Protocol)
    # ===================================================================
    st.divider()
    with st.expander("Save to Knowledge Base (Unified Report)", expanded=False):
        project_name = st.text_input(
            "Project Name", key="r_project_name",
            placeholder="e.g. Baby Spoons Review Analysis",
        )

        save_kb = st.button(
            "\U0001f4be Save Unified Report to KB",
            type="primary", key="r_save_kb",
            use_container_width=True,
        )

        if save_kb:
            if not project_name.strip():
                st.warning("Enter a project name.")
            else:
                happy_df = st.session_state.get("brand_dna_df")
                defect_df = st.session_state.get("defect_tracker_df")

                if (happy_df is None or happy_df.empty) and (
                    defect_df is None or defect_df.empty
                ):
                    st.warning("No analysis results to save. Run analysis first.")
                else:
                    kb = KnowledgeManager()
                    now = datetime.now().strftime("%Y-%m-%d %H:%M")
                    filename = kb.make_filename(project_name.strip())

                    md_lines = [
                        f"# Product Analysis: {project_name.strip()}",
                        "",
                        f"**Generated:** {now}",
                        f"**Total Reviews:** {total_reviews:,}",
                        f"**ASINs:** {len(asin_list)}",
                        f"**Happy (4-5\u2605):** {happy_count:,} | "
                        f"**Defect (1-3\u2605):** {defect_count:,}",
                        "",
                    ]

                    # ---- Happy Section ----
                    md_lines.append("---")
                    md_lines.append("")
                    md_lines.append("## Why People Buy (The Happy Flow)")
                    md_lines.append("")

                    if happy_df is not None and not happy_df.empty:
                        # Buying Factors table
                        buying_df = st.session_state.get("buying_factors_df")
                        if buying_df is not None and not buying_df.empty:
                            md_lines.append("### Buying Factors")
                            md_lines.append("")
                            md_lines.append(
                                "| Factor | Count | Quote |"
                            )
                            md_lines.append(
                                "|--------|-------|-------|"
                            )
                            agg = (
                                buying_df.groupby("factor", as_index=False)
                                .agg({"count": "sum", "quote": "first"})
                                .sort_values("count", ascending=False)
                            )
                            for _, row in agg.iterrows():
                                md_lines.append(
                                    f"| {row['factor']} "
                                    f"| {row['count']} "
                                    f"| {row['quote']} |"
                                )
                            md_lines.append("")

                        # Deep Dive per ASIN
                        md_lines.append("### Deep Dive Stories")
                        md_lines.append("")
                        for _, row in happy_df.iterrows():
                            md_lines.append(
                                f"#### {row.get('product_name', 'Unknown')}"
                            )
                            md_lines.append(
                                f"**ASIN:** {row.get('asin', '')}"
                            )
                            md_lines.append("")
                            md_lines.append(
                                f"> {row.get('primary_hook', '')}"
                            )
                            md_lines.append("")
                            if row.get("buying_factors", ""):
                                md_lines.append("**Buying Factors:**")
                                md_lines.append(row["buying_factors"])
                                md_lines.append("")
                            if row.get("cosmo_intents", ""):
                                md_lines.append("**COSMO Intents:**")
                                md_lines.append(row["cosmo_intents"])
                                md_lines.append("")
                            if row.get("rufus_keywords", ""):
                                md_lines.append(
                                    f"**Rufus Keywords:** {row['rufus_keywords']}"
                                )
                                md_lines.append("")
                            if row.get("eeat_stories", ""):
                                md_lines.append("**EEAT Stories:**")
                                md_lines.append(row["eeat_stories"])
                                md_lines.append("")
                            if row.get("competitor_wins", ""):
                                md_lines.append("**Competitor Wins:**")
                                md_lines.append(row["competitor_wins"])
                                md_lines.append("")
                            md_lines.append("---")
                            md_lines.append("")
                    else:
                        md_lines.append(
                            "*No Happy DNA results available.*"
                        )
                        md_lines.append("")

                    # ---- Defect Section ----
                    md_lines.append("## Why People Return (The Defect Flow)")
                    md_lines.append("")

                    if defect_df is not None and not defect_df.empty:
                        md_lines.append("### Issue Summary")
                        md_lines.append("")
                        md_lines.append(
                            "| Issue | Count | Quote | "
                            "Traffic Layer | Risk Tag | Share |"
                        )
                        md_lines.append(
                            "|-------|-------|-------|"
                            "---------------|----------|-------|"
                        )
                        for _, row in defect_df.iterrows():
                            share_pct = (
                                f"{row.get('issue_share', 0) * 100:.1f}%"
                            )
                            md_lines.append(
                                f"| {row.get('issue', '')} "
                                f"| {row.get('count', 0)} "
                                f"| {row.get('representative_quote', '')} "
                                f"| {row.get('impacted_traffic_layer', '')} "
                                f"| {row.get('risked_system_tag', '')} "
                                f"| {share_pct} |"
                            )
                        md_lines.append("")
                    else:
                        md_lines.append(
                            "*No Defect Tracker results available.*"
                        )
                        md_lines.append("")

                    md_content = "\n".join(md_lines)

                    # CSV: combine both DataFrames (tag with source)
                    csv_frames = []
                    if happy_df is not None and not happy_df.empty:
                        h = happy_df.copy()
                        h.insert(0, "report_type", "happy")
                        csv_frames.append(h)
                    if defect_df is not None and not defect_df.empty:
                        d = defect_df.copy()
                        d.insert(0, "report_type", "defect")
                        csv_frames.append(d)
                    combined_df = (
                        pd.concat(csv_frames, ignore_index=True)
                        if csv_frames
                        else pd.DataFrame()
                    )

                    kb.save_insight(
                        _KB_FOLDER, filename, md_content,
                        dataframe=combined_df,
                        project_slug=st.session_state.get("project_slug", ""),
                    )
                    csv_name = filename.replace(".md", ".csv")
                    st.success(
                        f"Saved unified report! "
                        f"\u2192 `{_KB_FOLDER}/{filename}` + `{csv_name}`"
                    )
