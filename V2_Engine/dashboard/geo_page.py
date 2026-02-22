"""
Source 6 — Auto Pilot GEO Writer

The main Auto Pilot GEO UI. A 7-pillar nested sidebar navigation shell that will host
Epics 1–4 of the SEO Writer Engine. Each pillar is a placeholder for an upcoming
Epic sprint.

Navigation: app.py radio -> "Source 6: Auto Pilot GEO"  -> sub-radio -> GEO pillars

Epics:
    Epic 0 — Intelligence Hub (hub_page.py)
    Epic 1 — Core Editor Shell (THIS FILE — shell ready, Writer TBD)
    Epic 2 — Discovery Grid + Keyword Galaxy
    Epic 3 — Writer Engine (AI Article Generator)
    Epic 4 — Output Library
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

_BOOKS_DEMO_PATH = os.path.join(_PROJECT_ROOT, "data", "demo", "sample_books", "books_demo.json")
_KB_GEO_FOLDER   = os.path.join(
    _PROJECT_ROOT, "V2_Engine", "knowledge_base", "storage", "6_seo_writer"
)


# ===========================================================================
# MAIN RENDER
# ===========================================================================

def render_geo_page() -> None:
    """Auto Pilot GEO Writer — nested 7-pillar navigation shell."""

    # -----------------------------------------------------------------------
    # Auto Pilot GEO Sidebar Navigation
    # -----------------------------------------------------------------------
    with st.sidebar:
        st.divider()
        st.caption("Auto Pilot GEO")
        geo_nav = st.radio(
            "Auto Pilot GEO",
            [
                "Dashboard",
                "Discovery Grid",
                "Keyword Galaxy",
                "Writer Engine",
                "Output Library",
                "Link Builder",
                "Site Health",
            ],
            key="geo_nav",
            label_visibility="collapsed",
        )
        st.divider()

    # -----------------------------------------------------------------------
    # Load Book (from session or disk)
    # -----------------------------------------------------------------------
    book: dict | None = st.session_state.get("current_book")
    if book is None and os.path.exists(_BOOKS_DEMO_PATH):
        try:
            with open(_BOOKS_DEMO_PATH, "r", encoding="utf-8") as f:
                book = json.load(f)
            st.session_state["current_book"] = book
        except Exception:
            pass

    # -----------------------------------------------------------------------
    # Route to pillar
    # -----------------------------------------------------------------------
    if geo_nav == "Dashboard":
        _render_dashboard(book)
    elif geo_nav == "Discovery Grid":
        _render_discovery_grid(book)
    elif geo_nav == "Keyword Galaxy":
        _render_keyword_galaxy(book)
    elif geo_nav == "Writer Engine":
        _render_writer_engine(book)
    elif geo_nav == "Output Library":
        _render_output_library()
    elif geo_nav == "Link Builder":
        _render_coming_soon("Link Builder", "Epic 4+", "Build internal links from semantic keyword clusters.")
    elif geo_nav == "Site Health":
        _render_coming_soon("Site Health", "Epic 4+", "Monitor GSC/Bing performance signals in one view.")


# ===========================================================================
# PILLAR RENDERERS
# ===========================================================================

def _render_dashboard(book: dict | None) -> None:
    st.header("Auto Pilot GEO Dashboard")
    st.caption("Your intelligence command center. A live snapshot of all data sources feeding the Writer Engine.")

    if book is None:
        st.warning(
            "No Intelligence Book loaded. Go to **Intelligence Hub** and click "
            "**Build Intelligence Book** first.",
        )
        return

    meta = book.get("meta", {})
    cat  = book.get("catalog_book", {})
    traf = book.get("traffic_book", {})
    rev  = book.get("reviews_book", {})
    ruf  = book.get("rufus_book", {})
    web  = book.get("webmaster_book", {})

    # --- Book banner ---
    st.info(
        f"**Active Book:** `{meta.get('product_slug', '—')}` / "
        f"`{meta.get('site_domain', '—')}` | "
        f"Mode: `{meta.get('mode', '—')}` | "
        f"Built: `{(meta.get('built_at', '') or '')[:10]}`"
    )

    # --- KPI row ---
    st.subheader("Intelligence Snapshot")
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Market ASINs",     len(cat.get("top_asins", [])))
    k2.metric("Keywords",         traf.get("summary", {}).get("total_keywords", 0))
    k3.metric("Happy Themes",     len(rev.get("happy_themes", [])))
    k4.metric("Rufus Traps",      len(ruf.get("trap_questions", [])))
    k5.metric("GEO Signals",      web.get("summary", {}).get("geo_signal_count", 0))

    st.divider()

    # --- Three column intel preview ---
    col_left, col_mid, col_right = st.columns(3)

    with col_left:
        st.subheader("Top Revenue Leaders")
        leaders = cat.get("revenue_leaders", [])[:5]
        for i, asin in enumerate(leaders, 1):
            rev_val = asin.get("parent_revenue")
            rev_str = f"${rev_val:,.0f}" if rev_val else "—"
            st.markdown(
                f"**{i}. {asin.get('brand', '—')}** "
                f"`{asin.get('asin', '')}` {rev_str}"
            )
        if not leaders:
            st.caption("No data.")

    with col_mid:
        st.subheader("Top Content Gaps")
        gaps = traf.get("content_gaps", [])[:5]
        for kw in gaps:
            vol = kw.get("volume") or 0
            st.markdown(f"- **{kw['keyword']}** — {vol:,} vol")
        if not gaps:
            st.caption("No gaps found — you may already rank for all keywords!")

    with col_right:
        st.subheader("Critical Rufus Traps")
        traps = ruf.get("trap_questions", [])[:5]
        for trap in traps:
            q = trap.get("question", "")
            st.markdown(f"- {q[:80]}{'...' if len(q) > 80 else ''}")
        if not traps:
            st.caption("No Rufus data loaded.")

    st.divider()

    # --- COSMO Intents + GEO Signals side by side ---
    col_cosmo, col_geo = st.columns(2)

    with col_cosmo:
        st.subheader("COSMO Intent Map")
        intents = rev.get("cosmo_intents", [])
        if intents:
            for intent in intents:
                st.markdown(f"- {intent}")
        else:
            st.caption("No COSMO intents loaded. Run Review Analysis first.")

    with col_geo:
        st.subheader("GEO Signals (AI Zero-Click)")
        signals = web.get("geo_signals", [])
        if signals:
            for sig in signals:
                st.markdown(
                    f"- **{sig.get('query', '—')}** — "
                    f"Pos #{sig.get('position', '?')} | "
                    f"{sig.get('impressions_7d', 0)} impr | "
                    f"{sig.get('insight', '')}"
                )
        else:
            st.caption("No GEO signals. Connect Source 5 Webmaster.")


def _render_discovery_grid(book: dict | None) -> None:
    st.header("Discovery Grid")
    st.caption(
        "Surface content opportunities from keyword clusters, topic gaps, "
        "and competitive white space. Powered by Cerebro traffic data + "
        "catalog intelligence."
    )

    _epic_status_banner("Epic 2", "Coming in next sprint. Book data is ready.")

    if book is None:
        st.warning("No Book loaded — go to Intelligence Hub first.")
        return

    traf = book.get("traffic_book", {})
    gaps = traf.get("content_gaps", [])
    trending = traf.get("trending", [])

    col_gap, col_trend = st.columns(2)

    with col_gap:
        st.subheader(f"Content Gaps ({len(gaps)})")
        st.caption("Keywords in your market where you have zero organic ranking.")
        if gaps:
            import pandas as pd
            display = [
                {
                    "Keyword":   k["keyword"],
                    "Volume":    k.get("volume") or 0,
                    "IQ Score":  k.get("iq_score") or 0,
                    "KW Sales":  k.get("keyword_sales") or 0,
                }
                for k in gaps
            ]
            st.dataframe(
                pd.DataFrame(display).sort_values("Volume", ascending=False),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.caption("No gaps found.")

    with col_trend:
        st.subheader(f"Trending Keywords ({len(trending)})")
        st.caption("Keywords with ≥ 20% search volume growth trend.")
        if trending:
            import pandas as pd
            display = [
                {
                    "Keyword":  k["keyword"],
                    "Volume":   k.get("volume") or 0,
                    "Trend %":  k.get("trend") or 0,
                }
                for k in trending
            ]
            st.dataframe(
                pd.DataFrame(display).sort_values("Trend %", ascending=False),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.caption("No trending keywords (trend ≥ 20%) found.")

    # Page 2 opportunities from GSC
    web = book.get("webmaster_book", {})
    p2_opps = web.get("gsc", {}).get("page_two_opportunities", [])
    if p2_opps:
        st.divider()
        st.subheader(f"Page 2 Quick Wins ({len(p2_opps)} keywords)")
        st.caption(
            "Google Search Console shows these queries ranking on page 2 "
            "(positions 11–20). Small optimization pushes = first page."
        )
        import pandas as pd
        p2_display = [
            {
                "Query":    item.get("query", ""),
                "Pos":      item.get("avg_pos_a", ""),
                "Impr":     item.get("total_impr_a", 0),
                "Page":     (item.get("pages") or [""])[0],
            }
            for item in p2_opps
        ]
        st.dataframe(pd.DataFrame(p2_display), use_container_width=True, hide_index=True)


def _render_keyword_galaxy(book: dict | None) -> None:
    st.header("Keyword Galaxy")
    st.caption(
        "3D/2D semantic scatter of your keyword universe. "
        "Find the 'empty black space' — underserved clusters with high volume and zero competition."
    )

    _epic_status_banner(
        "Epic 2",
        "Keyword Galaxy (PCA + Google text-embedding-004 + Plotly) coming in Epic 2 sprint. "
        "Keyword data is loaded and ready below."
    )

    if book is None:
        st.warning("No Book loaded — go to Intelligence Hub first.")
        return

    traf = book.get("traffic_book", {})
    all_kw = traf.get("top_keywords", [])
    if not all_kw:
        st.info("No keyword data available in this Book.")
        return

    # Preview the keyword table that will feed the Galaxy
    st.subheader(f"Keyword Input ({len(all_kw)} keywords ready for embedding)")
    st.caption(
        "These keywords will be embedded with `text-embedding-004`, "
        "reduced to 2D via PCA, and plotted as an interactive scatter."
    )
    import pandas as pd
    kw_display = [
        {
            "Keyword":   k["keyword"],
            "Volume":    k.get("volume") or 0,
            "Trend %":   k.get("trend") or 0,
            "Organic":   "" if k.get("is_organic") else "",
            "IQ Score":  k.get("iq_score") or 0,
        }
        for k in all_kw
    ]
    st.dataframe(pd.DataFrame(kw_display), use_container_width=True, hide_index=True)


def _render_writer_engine(book: dict | None) -> None:
    st.header("Writer Engine")
    st.caption(
        "AI-powered SEO article generator. The Book JSON is injected directly "
        "into the prompt — no RAG, no fragmentation, full cross-source context."
    )

    _epic_status_banner(
        "Epic 3",
        "5-stage sequential Writer Engine coming in Epic 3 sprint: "
        "Outline → Research → Draft → EEAT Enrichment → SEO Polish."
    )

    if book is None:
        st.warning("No Book loaded — go to Intelligence Hub first.")
        return

    # Preview what will be injected into the Writer prompt
    rev = book.get("reviews_book", {})
    ruf = book.get("rufus_book", {})

    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Prompt Ingredients Ready")
        ingredients = {
            "COSMO Intents":    len(rev.get("cosmo_intents", [])),
            "EEAT Proof Points": len(rev.get("eeat_proof", [])),
            "Rufus Traps":       len(ruf.get("trap_questions", [])),
            "Dealbreakers":      len(ruf.get("dealbreakers", [])),
            "Listing Gaps":      len(ruf.get("listing_gaps", [])),
            "Rufus Keywords":    len(rev.get("rufus_keywords", [])),
        }
        for label, count in ingredients.items():
            st.metric(label, count)

    with col_b:
        st.subheader("Target Article Formats")
        st.markdown(
            "- **Auto Pilot GEO Hybrid** — Markdown body + JSON-LD schema + semantic HTML H-tags\n"
            "- **Product Comparison** — vs competitor matrix (from catalog data)\n"
            "- **COSMO Intent Cluster** — one article per intent (BLW, Travel Feeding, etc.)\n"
            "- **EEAT Authority Piece** — built on real review proof points\n"
            "- **Rufus Defense** — FAQ article pre-empting top Rufus trap questions"
        )

    st.divider()
    st.info(
        "**Next steps for Epic 3:**  \n"
        "1. Build `writer_engine.py` with 5-function sequential chain  \n"
        "2. Add article format selector  \n"
        "3. Add keyword target input  \n"
        "4. Connect to Gemini 2.5 Pro via BYOK API key  \n"
        "5. Save output to Knowledge Base `6_seo_writer/` + `data/raw_zeabur_exports/`"
    )


def _render_output_library() -> None:
    st.header("Output Library")
    st.caption("Your generated articles, saved as Auto Pilot GEO Hybrid Markdown + JSON-LD + CSV metadata.")

    _epic_status_banner("Epic 4", "Output Library coming in Epic 4 sprint.")

    # Show any existing files in 6_seo_writer KB folder
    if os.path.isdir(_KB_GEO_FOLDER):
        files = [f for f in os.listdir(_KB_GEO_FOLDER) if f.endswith(".md")]
        if files:
            st.subheader(f"Saved Articles ({len(files)})")
            for fname in sorted(files, reverse=True):
                fpath = os.path.join(_KB_GEO_FOLDER, fname)
                size = os.path.getsize(fpath) / 1024
                col_name, col_size = st.columns([4, 1])
                with col_name:
                    if st.button(f"{fname}", key=f"lib_{fname}"):
                        with open(fpath, "r", encoding="utf-8") as f:
                            st.session_state["lib_view"] = f.read()
                with col_size:
                    st.caption(f"{size:.1f} KB")

            if "lib_view" in st.session_state:
                with st.expander("Article Preview", expanded=True):
                    st.markdown(st.session_state["lib_view"])
                    if st.button("Close"):
                        st.session_state.pop("lib_view")
                        st.rerun()
        else:
            st.info(f"No articles saved yet in `6_seo_writer/`. Generate your first article with the Writer Engine.")
    else:
        st.info("Output library folder will be created when you save your first article.")


def _render_coming_soon(pillar: str, epic: str, description: str) -> None:
    st.header(pillar)
    st.caption(description)
    _epic_status_banner(epic, f"{pillar} coming in a future sprint.")


# ===========================================================================
# SHARED UI HELPERS
# ===========================================================================

def _epic_status_banner(epic: str, message: str) -> None:
    """Show a styled 'coming soon' banner for unimplemented Epics."""
    st.info(f"**{epic} — Shell Ready:** {message}")
