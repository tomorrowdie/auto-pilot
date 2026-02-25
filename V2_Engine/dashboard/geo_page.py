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
        "and competitive white space. Select keywords to build your shortlist for the Galaxy."
    )

    if book is None:
        st.warning("No Book loaded — go to Intelligence Hub first.")
        return

    import pandas as pd

    # Init shortlist in session state
    if "discovery_shortlist" not in st.session_state:
        st.session_state["discovery_shortlist"] = []

    traf     = book.get("traffic_book", {})
    web      = book.get("webmaster_book", {})
    gaps     = traf.get("content_gaps", [])
    trending = traf.get("trending", [])
    p2_opps  = web.get("gsc", {}).get("page_two_opportunities", [])
    geo_sigs = web.get("geo_signals", [])

    # -----------------------------------------------------------------------
    # Sidebar — Shortlist Panel
    # -----------------------------------------------------------------------
    with st.sidebar:
        st.divider()
        shortlist = st.session_state["discovery_shortlist"]
        st.caption(f"Keyword Shortlist ({len(shortlist)})")
        if shortlist:
            for kw in shortlist[:8]:
                st.caption(f"• {kw}")
            if len(shortlist) > 8:
                st.caption(f"...+{len(shortlist) - 8} more")
            col_clr, col_lock = st.columns(2)
            if col_clr.button("Clear", key="disc_clr_side"):
                st.session_state["discovery_shortlist"] = []
                st.rerun()
            if col_lock.button("Send to Galaxy", key="disc_lock_side"):
                st.session_state["content_gap_targets"] = [
                    {"keyword": k} for k in shortlist
                ]
                st.success("Locked for Galaxy!")
        else:
            st.caption("No keywords selected yet.")
        st.divider()

    # -----------------------------------------------------------------------
    # Helper — add keywords to shortlist without duplicates
    # -----------------------------------------------------------------------
    def _add_to_shortlist(selected_list: list[str]) -> None:
        current = st.session_state["discovery_shortlist"]
        added   = sum(1 for k in selected_list if k not in current and not current.append(k))
        if added:
            st.session_state["discovery_shortlist"] = current
            st.rerun()

    # -----------------------------------------------------------------------
    # Four opportunity tabs
    # -----------------------------------------------------------------------
    tab_gaps, tab_trend, tab_p2, tab_geo = st.tabs([
        f"Content Gaps ({len(gaps)})",
        f"Trending ({len(trending)})",
        f"Page 2 Quick Wins ({len(p2_opps)})",
        f"GEO Signals ({len(geo_sigs)})",
    ])

    # --- Tab 1: Content Gaps ---
    with tab_gaps:
        st.caption("Keywords in your market where you have zero organic ranking.")
        if gaps:
            df = pd.DataFrame([
                {
                    "Keyword":  k["keyword"],
                    "Volume":   k.get("volume") or 0,
                    "IQ Score": k.get("iq_score") or 0,
                    "KW Sales": k.get("keyword_sales") or 0,
                }
                for k in gaps
            ]).sort_values("Volume", ascending=False)
            st.dataframe(df, use_container_width=True, hide_index=True)
            picked = st.multiselect(
                "Select keywords to add to shortlist:",
                [k["keyword"] for k in gaps],
                key="sel_gaps",
            )
            if st.button("Add to Shortlist", key="btn_gaps") and picked:
                _add_to_shortlist(picked)
        else:
            st.caption("No content gaps found.")

    # --- Tab 2: Trending ---
    with tab_trend:
        st.caption("Keywords with search volume growth trend.")
        if trending:
            df = pd.DataFrame([
                {
                    "Keyword": k["keyword"],
                    "Volume":  k.get("volume") or 0,
                    "Trend %": k.get("trend") or 0,
                }
                for k in trending
            ]).sort_values("Trend %", ascending=False)
            st.dataframe(df, use_container_width=True, hide_index=True)
            picked = st.multiselect(
                "Select keywords to add to shortlist:",
                [k["keyword"] for k in trending],
                key="sel_trend",
            )
            if st.button("Add to Shortlist", key="btn_trend") and picked:
                _add_to_shortlist(picked)
        else:
            st.caption("No trending keywords found.")

    # --- Tab 3: Page 2 Quick Wins ---
    with tab_p2:
        st.caption(
            "Google Search Console: queries ranking on page 2 (positions 11–20). "
            "Small push = first page."
        )
        if p2_opps:
            df = pd.DataFrame([
                {
                    "Query": item.get("query", ""),
                    "Avg Pos": item.get("avg_pos_a", ""),
                    "Impressions": item.get("total_impr_a", 0),
                    "Page": (item.get("pages") or [""])[0],
                }
                for item in p2_opps
            ])
            st.dataframe(df, use_container_width=True, hide_index=True)
            picked = st.multiselect(
                "Select queries to add to shortlist:",
                [item.get("query", "") for item in p2_opps if item.get("query")],
                key="sel_p2",
            )
            if st.button("Add to Shortlist", key="btn_p2") and picked:
                _add_to_shortlist(picked)
        else:
            st.caption("No page 2 opportunities. Connect Source 5 Webmaster for GSC data.")

    # --- Tab 4: GEO Signals ---
    with tab_geo:
        st.caption(
            "Bing GEO signals: queries with AI zero-click "
            "(impressions > 0, clicks = 0). AI is answering these — own the answer."
        )
        if geo_sigs:
            df = pd.DataFrame([
                {
                    "Query":          s.get("query", ""),
                    "Position":       s.get("position", ""),
                    "Impressions 7d": s.get("impressions_7d", 0),
                    "Insight":        s.get("insight", ""),
                }
                for s in geo_sigs
            ])
            st.dataframe(df, use_container_width=True, hide_index=True)
            picked = st.multiselect(
                "Select GEO queries to add to shortlist:",
                [s.get("query", "") for s in geo_sigs if s.get("query")],
                key="sel_geo",
            )
            if st.button("Add to Shortlist", key="btn_geo") and picked:
                _add_to_shortlist(picked)
        else:
            st.caption("No GEO signals. Connect Source 5 Webmaster for Bing GEO data.")

    # -----------------------------------------------------------------------
    # Bottom — current shortlist summary + proceed CTA
    # -----------------------------------------------------------------------
    current_shortlist = st.session_state["discovery_shortlist"]
    if current_shortlist:
        st.divider()
        st.subheader(f"Current Shortlist ({len(current_shortlist)} keywords)")
        st.dataframe(
            pd.DataFrame({"Keyword": current_shortlist}),
            use_container_width=True,
            hide_index=True,
        )
        col_info, col_act = st.columns([3, 1])
        with col_info:
            st.info(
                "Shortlist ready. Go to **Keyword Galaxy** to set your primary "
                "keyword and lock the selection for the Writer Engine."
            )
        with col_act:
            if st.button("Clear Shortlist", key="disc_clr_main"):
                st.session_state["discovery_shortlist"] = []
                st.rerun()


def _render_keyword_galaxy(book: dict | None) -> None:
    st.header("Keyword Galaxy")
    st.caption(
        "Set your primary target keyword, secondary support keywords, and COSMO intent. "
        "These are injected directly into the Writer Engine prompt — no RAG, full context."
    )

    if book is None:
        st.warning("No Book loaded — go to Intelligence Hub first.")
        return

    import pandas as pd

    traf = book.get("traffic_book", {})
    rev  = book.get("reviews_book", {})
    all_kw = traf.get("top_keywords", [])

    # Build keyword pool: shortlist first, then full traffic list
    shortlist    = st.session_state.get("discovery_shortlist", [])
    gap_targets  = st.session_state.get("content_gap_targets", [])
    shortlist_kws = list(dict.fromkeys(
        shortlist + [d["keyword"] for d in gap_targets if d.get("keyword")]
    ))

    pool = shortlist_kws.copy()
    for k in all_kw:
        if k["keyword"] not in pool:
            pool.append(k["keyword"])

    # Current locked values
    locked_primary   = st.session_state.get("selected_primary_kw", "")
    locked_secondary = st.session_state.get("selected_secondary_kws", [])
    locked_intent    = st.session_state.get("selected_intent", "")
    is_locked        = bool(locked_primary)

    # -----------------------------------------------------------------------
    # Locked-selection banner
    # -----------------------------------------------------------------------
    if is_locked:
        st.success(
            f"Selection locked for Writer Engine — Primary: **{locked_primary}**"
        )
        with st.expander("View locked selection"):
            st.markdown(f"**Primary keyword:** {locked_primary}")
            st.markdown(
                f"**Secondary keywords:** "
                f"{', '.join(locked_secondary) if locked_secondary else 'None'}"
            )
            st.markdown(f"**COSMO intent:** {locked_intent or 'None set'}")
        if st.button("Unlock and re-select", key="galaxy_unlock"):
            for key in ("selected_primary_kw", "selected_secondary_kws", "selected_intent"):
                st.session_state.pop(key, None)
            st.rerun()
        st.divider()

    # -----------------------------------------------------------------------
    # Selection UI  |  Stats preview
    # -----------------------------------------------------------------------
    col_sel, col_stats = st.columns([1, 1])

    with col_sel:
        st.subheader("Keyword Selection")

        if shortlist_kws:
            st.info(
                f"{len(shortlist_kws)} keywords from Discovery Grid shortlist "
                f"appear at the top of the list."
            )

        # --- Primary ---
        primary_idx = pool.index(locked_primary) if locked_primary in pool else 0
        primary_kw = st.selectbox(
            "Primary Target Keyword",
            options=pool if pool else ["— No keywords loaded —"],
            index=primary_idx,
            help="Main keyword for title, H1, and opening paragraph.",
            key="galaxy_primary",
        )

        # --- Secondary ---
        sec_pool = [k for k in pool if k != primary_kw]
        secondary_kws = st.multiselect(
            "Secondary Keywords (support cluster)",
            options=sec_pool,
            default=[k for k in locked_secondary if k in sec_pool],
            help="Supporting keywords for H2/H3 headers and body text.",
            key="galaxy_secondary",
        )

        # --- COSMO Intent ---
        intents = rev.get("cosmo_intents", [])
        if intents:
            intent_options = ["— None —"] + intents
            intent_idx = intent_options.index(locked_intent) if locked_intent in intent_options else 0
            selected_intent_raw = st.selectbox(
                "COSMO Intent (target use case)",
                options=intent_options,
                index=intent_idx,
                help="Buyer intent from Review Analysis — shapes article angle.",
                key="galaxy_intent",
            )
            selected_intent = "" if selected_intent_raw == "— None —" else selected_intent_raw
        else:
            st.caption("No COSMO intents available. Run Source 2 Review Analysis first.")
            selected_intent = ""

        st.divider()

        # --- Lock button ---
        if st.button("Lock Selection for Writer Engine", type="primary", key="galaxy_lock"):
            if pool and primary_kw != "— No keywords loaded —":
                st.session_state["selected_primary_kw"]    = primary_kw
                st.session_state["selected_secondary_kws"] = secondary_kws
                st.session_state["selected_intent"]        = selected_intent
                st.rerun()
            else:
                st.error("Please select a primary keyword first.")

    with col_stats:
        st.subheader("Keyword Stats")

        # Primary keyword metrics
        if pool and primary_kw and primary_kw != "— No keywords loaded —":
            primary_data = next((k for k in all_kw if k["keyword"] == primary_kw), None)
            if primary_data:
                m1, m2, m3 = st.columns(3)
                m1.metric("Search Volume", f"{primary_data.get('volume', 0):,}")
                m2.metric("IQ Score",      primary_data.get("iq_score", 0))
                m3.metric("Trend %",       f"{primary_data.get('trend', 0)}%")

        # Volume bar chart — top 20 keywords
        if all_kw:
            top20 = sorted(all_kw[:30], key=lambda k: k.get("volume") or 0, reverse=False)[:20]
            df_chart = pd.DataFrame([
                {"Keyword": k["keyword"][:28], "Volume": k.get("volume") or 0}
                for k in top20
            ]).set_index("Keyword")
            st.caption("Volume distribution — top 20 keywords")
            st.bar_chart(df_chart["Volume"])

    # -----------------------------------------------------------------------
    # Full keyword table
    # -----------------------------------------------------------------------
    st.divider()
    st.subheader(f"Full Keyword Pool ({len(all_kw)} keywords)")
    if all_kw:
        kw_display = [
            {
                "Keyword":  k["keyword"],
                "Volume":   k.get("volume") or 0,
                "Trend %":  k.get("trend") or 0,
                "Organic":  "Yes" if k.get("is_organic") else "",
                "IQ Score": k.get("iq_score") or 0,
            }
            for k in all_kw
        ]
        st.dataframe(pd.DataFrame(kw_display), use_container_width=True, hide_index=True)
    else:
        st.info("No keyword data available. Run Source 1 (Cerebro Traffic) first.")


def _render_writer_engine(book: dict | None) -> None:
    st.header("Writer Engine")
    st.caption(
        "3-stage AI article generator. Book JSON is injected directly into each prompt "
        "— no RAG, no fragmentation, full cross-source context."
    )

    if book is None:
        st.warning("No Book loaded — go to Intelligence Hub first.")
        return

    # Lazy-import the chain module
    try:
        from V2_Engine.processors.source_6_seo.llm_chain import (
            run_part0, run_part1, run_part2, md_to_html,
        )
        _chain_ok = True
    except ImportError as _e:
        _chain_ok = False
        st.error(f"LLM chain module not found: {_e}")

    # Pre-load from Epic 1 session state
    primary_kw    = st.session_state.get("selected_primary_kw", "")
    secondary_kws = st.session_state.get("selected_secondary_kws", [])
    intent        = st.session_state.get("selected_intent", "")
    writer_result = st.session_state.get("writer_result")

    rev = book.get("reviews_book", {})
    ruf = book.get("rufus_book", {})

    # -----------------------------------------------------------------------
    # Split screen: Left (Controls) | Right (Canvas)
    # -----------------------------------------------------------------------
    col_left, col_right = st.columns([1, 2])

    # ===================================================================
    # LEFT COLUMN — Wizard / Controls
    # ===================================================================
    with col_left:
        st.subheader("Article Setup")

        # Mode toggle
        mode = st.radio(
            "Mode",
            ["Simple", "Advanced"],
            horizontal=True,
            key="writer_mode_radio",
            label_visibility="collapsed",
        )
        st.divider()

        # --- Keyword target (auto-hydrated from Epic 1) ---
        st.caption("Keyword Target")
        if primary_kw:
            st.success(f"Primary: **{primary_kw}**")
            if secondary_kws:
                sec_preview = ", ".join(secondary_kws[:3])
                suffix = f" +{len(secondary_kws) - 3} more" if len(secondary_kws) > 3 else ""
                st.caption(f"Secondary: {sec_preview}{suffix}")
            if intent:
                st.caption(f"Intent: {intent}")
            manual_primary = primary_kw
        else:
            st.warning("No keyword locked. Go to **Keyword Galaxy** first, or enter manually below.")
            manual_primary = st.text_input(
                "Primary Keyword (manual override)",
                placeholder="e.g. baby spoon",
                key="writer_primary_manual",
            )

        effective_primary = manual_primary  # may be from session state or manual entry

        # --- Advanced Mode extra fields ---
        brand    = ""
        industry = ""
        audience = ""
        tone     = "Informative"
        art_len  = 1500
        api_key  = ""
        model    = "mock"

        if mode == "Advanced":
            st.divider()
            st.caption("Brand & Audience")
            brand    = st.text_input("Brand Name",       placeholder="e.g. BabyNosh",              key="w_brand")
            industry = st.text_input("Industry / Niche", placeholder="e.g. Baby Feeding",           key="w_industry")
            audience = st.text_input("Target Audience",  placeholder="e.g. New parents, 25–40",     key="w_audience")
            tone     = st.selectbox(
                "Tone of Voice",
                ["Informative", "Conversational", "Expert / Authority", "Persuasive", "Friendly & Warm"],
                key="w_tone",
            )
            art_len = st.selectbox(
                "Article Length (words)",
                [800, 1200, 1500, 2000, 2500, 3000],
                index=2,
                key="w_length",
            )
            st.divider()
            st.caption("LLM Settings (BYOK)")
            api_key = st.text_input(
                "API Key",
                type="password",
                placeholder="Gemini or Qwen API key",
                key="w_api_key",
            )
            model_choice = st.selectbox(
                "Model",
                ["mock (UI preview)", "gemini-pro", "gemini-flash", "qwen"],
                key="w_model",
            )
            model   = "mock" if model_choice == "mock (UI preview)" else model_choice
            api_key = "" if model == "mock" else api_key

        # --- Prompt ingredient summary ---
        st.divider()
        with st.expander("Prompt Ingredients"):
            ma, mb = st.columns(2)
            ma.metric("COSMO Intents",  len(rev.get("cosmo_intents", [])))
            ma.metric("EEAT Proof",     len(rev.get("eeat_proof", [])))
            ma.metric("Rufus Traps",    len(ruf.get("trap_questions", [])))
            mb.metric("Dealbreakers",   len(ruf.get("dealbreakers", [])))
            mb.metric("Listing Gaps",   len(ruf.get("listing_gaps", [])))
            mb.metric("Rufus Keywords", len(rev.get("rufus_keywords", [])))

        st.divider()

        # Generate button (disabled until a keyword is available)
        generate_clicked = st.button(
            "Generate SEO Article",
            type="primary",
            key="writer_generate",
            use_container_width=True,
            disabled=(not bool(effective_primary) or not _chain_ok),
        )

    # ===================================================================
    # RIGHT COLUMN — Canvas
    # ===================================================================
    with col_right:

        # ----------------------------------------------------------------
        # A) GENERATE flow — runs inline so st.status renders in real-time
        # ----------------------------------------------------------------
        if generate_clicked and effective_primary and _chain_ok:
            inputs = {
                "primary_kw":     effective_primary,
                "secondary_kws":  secondary_kws,
                "intent":         intent,
                "brand":          brand,
                "industry":       industry,
                "audience":       audience or "customers",
                "tone":           tone,
                "article_length": art_len,
            }
            with st.status("Generating SEO article...", expanded=True) as status:
                st.write("Stage 1/3 — Building content architecture brief...")
                p0 = run_part0(inputs, api_key, model)

                st.write("Stage 2/3 — Generating article outline...")
                p1 = run_part1(inputs, p0, api_key, model)

                st.write("Stage 3/3 — Writing full article draft...")
                p2 = run_part2(inputs, p1, api_key, model)

                html = md_to_html(p2)
                status.update(label="Article complete!", state="complete", expanded=False)

            st.session_state["writer_result"] = {
                "part0":      p0,
                "part1":      p1,
                "markdown":   p2,
                "html":       html,
                "primary_kw": effective_primary,
            }
            st.rerun()

        # ----------------------------------------------------------------
        # B) RESULT view — shown after generation
        # ----------------------------------------------------------------
        elif writer_result:
            md_text   = writer_result.get("markdown", "")
            html_text = writer_result.get("html", "")
            art_kw    = writer_result.get("primary_kw", effective_primary)
            safe_slug = (art_kw or "article").replace(" ", "_")

            # Output tabs
            tab_visual, tab_html, tab_outline = st.tabs(["Visual", "</> HTML", "Outline"])

            with tab_visual:
                st.markdown(md_text)

            with tab_html:
                st.code(html_text, language="html")

            with tab_outline:
                outline = writer_result.get("part1", "")
                if outline:
                    st.markdown(outline)
                else:
                    st.caption("Outline not captured in this run.")

            # ---- Action Toolbar ----------------------------------------
            st.divider()
            st.caption("Actions")

            row1 = st.columns(4)
            row2 = st.columns(4)

            # Row 1 — Copy / Download
            with row1[0]:
                with st.expander("Copy Markdown"):
                    st.code(md_text, language="markdown")

            with row1[1]:
                with st.expander("Copy HTML"):
                    st.code(html_text, language="html")

            with row1[2]:
                st.download_button(
                    "Download .md",
                    data=md_text,
                    file_name=f"{safe_slug}.md",
                    mime="text/markdown",
                    use_container_width=True,
                    key="dl_md",
                )

            with row1[3]:
                st.download_button(
                    "Download .html",
                    data=html_text,
                    file_name=f"{safe_slug}.html",
                    mime="text/html",
                    use_container_width=True,
                    key="dl_html",
                )

            # Row 2 — Navigation / Control
            with row2[0]:
                if st.button("Regenerate", use_container_width=True, key="tb_regen"):
                    st.session_state.pop("writer_result", None)
                    st.rerun()

            with row2[1]:
                if st.button("Write Another", use_container_width=True, key="tb_another"):
                    for _k in (
                        "writer_result", "selected_primary_kw",
                        "selected_secondary_kws", "selected_intent",
                        "discovery_shortlist",
                    ):
                        st.session_state.pop(_k, None)
                    st.session_state["geo_nav"] = "Keyword Galaxy"
                    st.rerun()

            with row2[2]:
                if st.button("Discover More Ideas", use_container_width=True, key="tb_discover"):
                    st.session_state["geo_nav"] = "Discovery Grid"
                    st.rerun()

            with row2[3]:
                if st.button("Go to Library", use_container_width=True, key="tb_library"):
                    st.session_state["geo_nav"] = "Output Library"
                    st.rerun()

            # Connect Publisher placeholder
            with st.expander("Connect Publisher"):
                st.caption(
                    "CMS integrations (WordPress, Shopify, Webflow) are coming in Epic 4. "
                    "For now, copy the HTML above and paste into your CMS editor."
                )

        # ----------------------------------------------------------------
        # C) IDLE state — no result yet
        # ----------------------------------------------------------------
        else:
            if not effective_primary:
                st.info(
                    "**No keyword selected.**  \n"
                    "Go to **Keyword Galaxy** to lock your primary keyword, "
                    "then return here to generate your article."
                )
                if st.button("Go to Keyword Galaxy", key="writer_go_galaxy"):
                    st.session_state["geo_nav"] = "Keyword Galaxy"
                    st.rerun()
            else:
                st.info(
                    f"**Ready to generate.**  \n"
                    f"Primary keyword locked: **{effective_primary}**  \n"
                    f"Click **Generate SEO Article** on the left to start the 3-stage pipeline."
                )

            # Show ingredient readiness
            st.divider()
            st.caption("Prompt Ingredients Available")
            c1, c2, c3 = st.columns(3)
            c1.metric("COSMO Intents", len(rev.get("cosmo_intents", [])))
            c2.metric("Rufus Traps",   len(ruf.get("trap_questions", [])))
            c3.metric("EEAT Proof",    len(rev.get("eeat_proof", [])))

            if not primary_kw:
                st.divider()
                st.caption("Pipeline preview (stages will execute in order):")
                st.markdown(
                    "1. **Stage 1 — Architecture Brief** — keyword + brand + audience → content strategy\n"
                    "2. **Stage 2 — Article Outline** — strategy → H-tag structure + section plan\n"
                    "3. **Stage 3 — Full Draft** — outline → complete, publish-ready Markdown article"
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
