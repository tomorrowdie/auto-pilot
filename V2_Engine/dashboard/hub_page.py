"""
Source 6 — Intelligence Hub (Epic 0)

The Master Uploader. Assembles the canonical Book JSON from all upstream sources
(Catalog, Traffic, Reviews, Rufus, Webmaster) and gives the user a unified view
of their intelligence before entering the Harbor SEO Writer.

Navigation: app.py radio -> "Source 6: Harbor"  -> sub-radio -> "Intelligence Hub"
"""

from __future__ import annotations

import json
import os
import sys

import streamlit as st

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from V2_Engine.processors.source_6_seo.book_builder import build_book

_RAW_EXPORT_DIR = os.path.join(_PROJECT_ROOT, "data", "raw_zeabur_exports")
_BOOKS_DEMO_PATH = os.path.join(_PROJECT_ROOT, "data", "books_demo.json")


# ===========================================================================
# MAIN RENDER
# ===========================================================================

def render_hub_page() -> None:
    st.header("Intelligence Hub")
    st.caption(
        "Assemble your Book — the unified intelligence brief that powers the "
        "Harbor SEO Writer Engine. All upstream sources feed into a single, "
        "structured JSON ready for AI-driven article generation."
    )

    # -----------------------------------------------------------------------
    # Project Config
    # -----------------------------------------------------------------------
    with st.expander("Project Configuration", expanded=True):
        col_slug, col_domain = st.columns(2)
        with col_slug:
            product_slug = st.text_input(
                "Product Slug",
                value=st.session_state.get("hub_product_slug", "baby_spoon"),
                placeholder="e.g. baby_spoon",
                help="snake_case identifier matching your export file prefix.",
                key="hub_product_slug_input",
            )
        with col_domain:
            site_domain = st.text_input(
                "Site Domain",
                value=st.session_state.get("hub_site_domain", ""),
                placeholder="e.g. mybrand.com",
                help="Domain used to locate Bing and GSC webmaster files.",
                key="hub_site_domain_input",
            )

        mode = st.radio(
            "Data Source",
            ["demo", "live"],
            horizontal=True,
            help=(
                "**demo** — reads from `data/raw_zeabur_exports/`  \n"
                "**live** — reads from `knowledge_base/storage/` (latest saved runs)"
            ),
            key="hub_mode",
        )

        build_btn = st.button(
            "Build Intelligence Book",
            type="primary",
            use_container_width=True,
            key="hub_build_btn",
        )

    # -----------------------------------------------------------------------
    # Build / Load Book
    # -----------------------------------------------------------------------
    if build_btn:
        slug = product_slug.strip() or "demo"
        domain = site_domain.strip()
        st.session_state["hub_product_slug"] = slug
        st.session_state["hub_site_domain"] = domain

        with st.spinner("Assembling Intelligence Book..."):
            try:
                book = build_book(
                    product_slug=slug,
                    site_domain=domain,
                    mode=mode,
                )
                st.session_state["current_book"] = book

                # Auto-save books_demo.json when built in demo mode
                if mode == "demo":
                    with open(_BOOKS_DEMO_PATH, "w", encoding="utf-8") as f:
                        json.dump(book, f, indent=2, ensure_ascii=False, default=str)

                st.success(
                    f"Book assembled successfully — "
                    f"{_book_size_label(book)} of intelligence ready."
                )
            except Exception as e:
                st.error(f"Book assembly failed: {e}")
                return

    # Try to load from session state first, then fallback to books_demo.json
    book: dict | None = st.session_state.get("current_book")
    if book is None and os.path.exists(_BOOKS_DEMO_PATH):
        try:
            with open(_BOOKS_DEMO_PATH, "r", encoding="utf-8") as f:
                book = json.load(f)
            st.session_state["current_book"] = book
        except Exception:
            pass

    if book is None:
        st.info(
            "No Book assembled yet. Configure your project above and click "
            "**Build Intelligence Book** to get started."
        )
        return

    # -----------------------------------------------------------------------
    # Book Header
    # -----------------------------------------------------------------------
    meta = book.get("meta", {})
    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Product", meta.get("product_slug", "—"))
    c2.metric("Domain", meta.get("site_domain", "—") or "—")
    c3.metric("Mode", meta.get("mode", "—"))
    c4.metric("Built", (meta.get("built_at", "") or "")[:10] or "—")

    # -----------------------------------------------------------------------
    # Source Health Status Row
    # -----------------------------------------------------------------------
    st.subheader("Source Health")
    h1, h2, h3, h4, h5 = st.columns(5)

    def _status_badge(source_book: dict) -> str:
        status = source_book.get("status", "?")
        if status == "ok":
            return "ok"
        elif status == "no_data":
            return "no data"
        else:
            return f"error"

    def _col_metric(col, label: str, source_book: dict, count_label: str, count: int) -> None:
        status = _status_badge(source_book)
        icon = "" if source_book.get("status") == "ok" else ""
        col.metric(f"{icon} {label}", f"{count:,} {count_label}", delta=status if status != "ok" else None)

    cat = book.get("catalog_book", {})
    traf = book.get("traffic_book", {})
    rev = book.get("reviews_book", {})
    ruf = book.get("rufus_book", {})
    web = book.get("webmaster_book", {})

    h1.metric("Catalog",    f"{len(cat.get('top_asins', []))} ASINs",
              delta=None if cat.get('status') == 'ok' else cat.get('status'))
    h2.metric("Traffic",    f"{traf.get('summary', {}).get('total_keywords', 0)} keywords",
              delta=None if traf.get('status') == 'ok' else traf.get('status'))
    h3.metric("Reviews",    f"{len(rev.get('happy_themes', []))} themes",
              delta=None if rev.get('status') == 'ok' else rev.get('status'))
    h4.metric("Rufus",      f"{len(ruf.get('trap_questions', []))} traps",
              delta=None if ruf.get('status') == 'ok' else ruf.get('status'))
    h5.metric("Webmaster",  f"{web.get('summary', {}).get('geo_signal_count', 0)} GEO signals",
              delta=None if web.get('status') == 'ok' else web.get('status'))

    # -----------------------------------------------------------------------
    # Deep-Dive Tabs
    # -----------------------------------------------------------------------
    st.divider()
    tab_cat, tab_traf, tab_rev, tab_ruf, tab_web, tab_json = st.tabs([
        "Catalog", "Traffic", "Reviews", "Rufus", "Webmaster", "Raw JSON"
    ])

    # --- Catalog Tab ---
    with tab_cat:
        st.subheader("Market Summary")
        ms = cat.get("market_summary", {})
        if ms:
            r1, r2, r3, r4 = st.columns(4)
            r1.metric("Total Brands",   f"{int(ms['total_brands']):,}"      if ms.get("total_brands")    else "—")
            r2.metric("Total Products", f"{int(ms['total_products']):,}"     if ms.get("total_products")  else "—")
            r3.metric("HHI Score",      f"{int(ms['hhi_score']):,}"          if ms.get("hhi_score")       else "—")
            r4.metric("Classification", ms.get("hhi_classification", "—"))
            p1, p2, p3, p4 = st.columns(4)
            p1.metric("Avg Price",      f"${ms['avg_price']:.2f}"            if ms.get("avg_price")       else "—")
            p2.metric("Price Range",    f"${ms.get('price_min', 0):.2f} – ${ms.get('price_max', 0):.2f}"
                                        if ms.get("price_min") else "—")
            p3.metric("Avg ASIN Rev",   f"${ms['avg_asin_revenue']:,.0f}"    if ms.get("avg_asin_revenue")else "—")
            p4.metric("Avg Rating",     f"{ms['avg_rating']:.2f}"            if ms.get("avg_rating")      else "—")

        st.subheader(f"Revenue Leaders (Top {len(cat.get('revenue_leaders', []))})")
        if cat.get("revenue_leaders"):
            import pandas as pd
            rl_df = pd.DataFrame(cat["revenue_leaders"])
            st.dataframe(rl_df, use_container_width=True, hide_index=True)

    # --- Traffic Tab ---
    with tab_traf:
        ts = traf.get("summary", {})
        t1, t2, t3, t4 = st.columns(4)
        t1.metric("Total Keywords", ts.get("total_keywords", 0))
        t2.metric("Organic",        ts.get("organic_count", 0))
        t3.metric("Content Gaps",   ts.get("gap_count", 0))
        t4.metric("Trending (≥20%)", ts.get("trending_count", 0))

        if traf.get("top_keywords"):
            import pandas as pd
            kw_df = pd.DataFrame(traf["top_keywords"])
            st.subheader("All Keywords")
            st.dataframe(kw_df, use_container_width=True, hide_index=True)

        if traf.get("content_gaps"):
            st.subheader("Content Gaps (Not Ranking)")
            st.dataframe(pd.DataFrame(traf["content_gaps"]), use_container_width=True, hide_index=True)

    # --- Reviews Tab ---
    with tab_rev:
        rs = rev.get("summary", {})
        rv1, rv2, rv3, rv4 = st.columns(4)
        rv1.metric("ASINs Analyzed",  rs.get("asin_count", 0))
        rv2.metric("Happy Themes",    rs.get("happy_theme_count", 0))
        rv3.metric("COSMO Intents",   rs.get("cosmo_intent_count", 0))
        rv4.metric("Has Defect Data", "Yes" if rs.get("has_defect_data") else "No")

        if rev.get("happy_themes"):
            st.subheader("Buying Factors (Happy Themes)")
            import pandas as pd
            ht_df = pd.DataFrame(rev["happy_themes"])
            st.dataframe(ht_df, use_container_width=True, hide_index=True)

        if rev.get("cosmo_intents"):
            st.subheader("COSMO Intents")
            for intent in rev["cosmo_intents"]:
                st.markdown(f"- {intent}")

        if rev.get("rufus_keywords"):
            st.subheader("Rufus Keywords")
            st.write(", ".join(rev["rufus_keywords"]))

    # --- Rufus Tab ---
    with tab_ruf:
        rfs = ruf.get("summary", {})
        rfc1, rfc2, rfc3, rfc4 = st.columns(4)
        rfc1.metric("Trap Questions",  rfs.get("trap_count", 0))
        rfc2.metric("Dealbreakers",    rfs.get("dealbreaker_count", 0))
        rfc3.metric("Listing Gaps",    rfs.get("gap_count", 0))
        rfc4.metric("Coverage Score",  ruf.get("listing_coverage_score") or "—")

        if ruf.get("trap_questions"):
            import pandas as pd
            st.subheader("Trap Questions")
            st.dataframe(pd.DataFrame(ruf["trap_questions"]), use_container_width=True, hide_index=True)

        if ruf.get("listing_gaps"):
            st.subheader("Listing Gaps")
            st.dataframe(pd.DataFrame(ruf["listing_gaps"]), use_container_width=True, hide_index=True)

        if ruf.get("dealbreakers"):
            st.subheader("Dealbreakers")
            st.dataframe(pd.DataFrame(ruf["dealbreakers"]), use_container_width=True, hide_index=True)

    # --- Webmaster Tab ---
    with tab_web:
        ws = web.get("summary", {})
        wc1, wc2, wc3, wc4 = st.columns(4)
        wc1.metric("GSC Keywords (28d)", ws.get("gsc_new_keywords_28d", 0))
        wc2.metric("GSC Keywords (7d)",  ws.get("gsc_new_keywords_7d", 0))
        wc3.metric("Page 2 Opps",        ws.get("gsc_page_two_count", 0))
        wc4.metric("GEO Signals",        ws.get("geo_signal_count", 0))

        if web.get("geo_signals"):
            st.subheader("GEO Signals (AI Zero-Click)")
            import pandas as pd
            st.dataframe(pd.DataFrame(web["geo_signals"]), use_container_width=True, hide_index=True)

        if web.get("bing", {}).get("top_queries"):
            st.subheader("Bing Top Queries (28d)")
            st.dataframe(
                pd.DataFrame(web["bing"]["top_queries"]),
                use_container_width=True, hide_index=True
            )

        if web.get("gsc", {}).get("new_keywords"):
            st.subheader("GSC New Keywords (28d)")
            gsc_df = pd.DataFrame(web["gsc"]["new_keywords"])
            display_cols = [c for c in ["query", "total_impr_a", "avg_pos_a", "pages"] if c in gsc_df.columns]
            st.dataframe(gsc_df[display_cols], use_container_width=True, hide_index=True)

    # --- Raw JSON Tab ---
    with tab_json:
        st.subheader("Raw Book JSON")
        st.caption("This is the canonical bundle injected into the Writer Engine prompt.")

        col_dl, col_size = st.columns([3, 1])
        json_str = json.dumps(book, indent=2, ensure_ascii=False, default=str)
        with col_dl:
            st.download_button(
                "Download books_demo.json",
                data=json_str.encode("utf-8"),
                file_name=f"book_{meta.get('product_slug', 'demo')}.json",
                mime="application/json",
            )
        with col_size:
            st.metric("Size", f"{len(json_str) / 1024:.1f} KB")

        with st.expander("Preview (first 200 lines)", expanded=False):
            preview_lines = json_str.split("\n")[:200]
            st.code("\n".join(preview_lines), language="json")


# ===========================================================================
# HELPERS
# ===========================================================================

def _book_size_label(book: dict) -> str:
    size = len(json.dumps(book, default=str)) / 1024
    return f"{size:.1f} KB"
