"""
GEO Writer Engine

The main GEO Writer UI. A 7-pillar nested sidebar navigation shell that hosts
Epics 1–4 of the SEO Writer Engine. Each pillar is a placeholder for an upcoming
Epic sprint.

Navigation: app.py radio -> "GEO Writer Engine" -> sub-radio -> GEO pillars

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
    st.header("Auto Pilot GEO")
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
            md_to_html, run_part0, run_part1, run_part2, parse_structured_output,
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
    # LEFT COLUMN — Controls
    # ===================================================================
    with col_left:
        st.subheader("GEO Writer")
        st.caption("Configure your article, then click Generate.")

        # ── KEYWORD TARGET ───────────────────────────────────────────────
        st.markdown("**Keyword Target**")
        if primary_kw:
            st.success(f"**{primary_kw}**")
            if secondary_kws:
                sec_preview = ", ".join(secondary_kws[:3])
                suffix = f" +{len(secondary_kws) - 3} more" if len(secondary_kws) > 3 else ""
                st.caption(f"Secondary: {sec_preview}{suffix}")
            if intent:
                st.caption(f"Intent: {intent}")
            manual_primary = primary_kw
        else:
            st.warning("No keyword locked — go to **Keyword Galaxy** first.")
            manual_primary = st.text_input(
                "Primary Keyword",
                placeholder="e.g. baby spoon",
                key="writer_primary_manual",
            )

        effective_primary = (manual_primary or "").strip()

        # ── BRAND IDENTITY ───────────────────────────────────────────────
        with st.expander("🏷️ Brand Identity"):
            brand          = st.text_input("Brand Name",        placeholder="e.g. BabyNosh",                  key="w_brand")
            industry       = st.text_input("Industry / Niche",  placeholder="e.g. Baby Feeding Products",     key="w_industry")
            founded        = st.text_input("Founded",           placeholder="e.g. Austin TX, 2018",           key="w_founded")
            core_values    = st.text_area( "Core Values",       placeholder="e.g. Safety, Simplicity, Joy",   key="w_core_values",    height=68)
            brand_heritage = st.text_area( "Brand Heritage",    placeholder="Brief origin story...",          key="w_brand_heritage", height=68)
            mission        = st.text_input("Mission Statement", placeholder="e.g. Healthier meals for babies", key="w_mission")
            brand_story    = st.text_area( "Brand Story",       placeholder="Longer brand narrative...",      key="w_brand_story",    height=80)
            distribution   = st.text_input("Distribution",      placeholder="e.g. Amazon, DTC website",       key="w_distribution")
            audience       = st.text_input("Target Audience",   placeholder="e.g. New parents, 25–40",        key="w_audience")
            website_base   = st.text_input("Website URL",       placeholder="e.g. https://babynosh.com",      key="w_website_base")

        # ── CONTENT PROJECT ──────────────────────────────────────────────
        with st.expander("📋 Content Project"):
            main_topic      = st.text_input("Main Topic",      placeholder="e.g. Best Baby Spoons 2025",  key="w_main_topic")
            target_location = st.text_input("Target Location", placeholder="e.g. United States",          key="w_target_location")
            _cl_options = [
                "CLUSTER_L3 — Cluster (1,500–3,000w)",
                "PILLAR_L1 — Pillar (3,000–6,000w)",
                "SUBPILLAR_L2 — Sub-Pillar (2,000–4,000w)",
                "SUPPORT_L4 — Support (800–1,500w)",
            ]
            _cl_sel     = st.selectbox("Content Level", _cl_options, key="w_content_level")
            content_level_val = _cl_sel.split(" — ")[0]
            tone = st.selectbox(
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

        # ── SITE ARCHITECTURE ────────────────────────────────────────────
        with st.expander("🔗 Site Architecture"):
            main_pillar_page = st.text_input("Main Pillar Page", placeholder="e.g. Baby Feeding Guide",  key="w_main_pillar_page")
            sub_pillar_page  = st.text_input("Sub-Pillar Page",  placeholder="e.g. Best Baby Utensils",  key="w_sub_pillar_page")
            sister_clusters  = st.text_input("Sister Clusters",  placeholder="e.g. silicone spoons, self-feeding", key="w_sister_clusters")

        # ── LLM (wired from global API key vault) ────────────────────────
        from V2_Engine.saas_core.auth import auth_manager as _am
        _vault_uid = st.session_state.get("user_id", "dev_admin")
        api_key    = _am.get_api_key(_vault_uid, "google") or ""
        model      = "gemini-3.1-pro-preview" if api_key else "mock"
        if api_key:
            st.caption("LLM: Gemini 3.1 Pro ✓")
        else:
            st.warning(
                "No Google API key found — running in mock preview mode.  \n"
                "Add your Gemini key in the **API Keys** sidebar."
            )

        # ── PROMPT INGREDIENTS ───────────────────────────────────────────
        with st.expander("🧪 Prompt Ingredients"):
            ma, mb = st.columns(2)
            ma.metric("COSMO Intents",  len(rev.get("cosmo_intents", [])))
            ma.metric("EEAT Proof",     len(rev.get("eeat_proof", [])))
            ma.metric("Rufus Traps",    len(ruf.get("trap_questions", [])))
            mb.metric("Dealbreakers",   len(ruf.get("dealbreakers", [])))
            mb.metric("Listing Gaps",   len(ruf.get("listing_gaps", [])))
            mb.metric("Rufus KWs",      len(rev.get("rufus_keywords", [])))

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
        if generate_clicked and not effective_primary:
            st.error(
                "**No keyword provided.** Lock a primary keyword in **Keyword Galaxy** "
                "or type one manually in the left panel before generating."
            )

        elif generate_clicked and effective_primary and _chain_ok:
            inputs = {
                # Keyword target
                "primary_kw":        effective_primary,
                "primary_keyword":   effective_primary,
                "secondary_kws":     secondary_kws,
                "secondary_keyword": ", ".join(secondary_kws) if isinstance(secondary_kws, list) else str(secondary_kws),
                "intent":            intent,
                # Brand identity
                "brand":             brand,
                "industry":          industry,
                "founded":           founded,
                "core_values":       core_values,
                "brand_heritage":    brand_heritage,
                "mission":           mission,
                "brand_story":       brand_story,
                "distribution":      distribution,
                "audience":          audience or "customers",
                "target_audience":   audience or "customers",
                "website_base":      website_base,
                # Content project
                "main_topic":        main_topic or effective_primary,
                "target_location":   target_location,
                "content_level":     content_level_val,
                "tone":              tone,
                "article_length":    art_len,
                # Site architecture
                "main_pillar_page":  main_pillar_page,
                "sub_pillar_page":   sub_pillar_page,
                "sister_clusters":   sister_clusters,
            }
            with st.status("Stage 1/3 — Building content architecture brief...", expanded=True) as status:
                p0 = run_part0(inputs, api_key, model, book=book)

                status.update(label="Stage 2/3 — Generating article outline...", state="running")
                p1 = run_part1(inputs, p0, api_key, model, book=book)

                status.update(label="Stage 3/3 — Writing full article draft...", state="running")
                p2 = run_part2(inputs, p1, api_key, model, book=book)

                parsed = parse_structured_output(p2)
                html   = md_to_html(parsed["body"] or p2)
                status.update(label="Article complete!", state="complete", expanded=False)

            st.session_state["writer_result"] = {
                "title":          parsed["title"],
                "body":           parsed["body"],
                "tech_seo":       parsed["tech_seo"],
                "part0":          p0,
                "part1":          p1,
                "markdown":       p2,
                "clean_markdown": parsed["body"],
                "html":           html,
                "primary_kw":     effective_primary,
            }
            st.rerun()

        # ----------------------------------------------------------------
        # B-pre) STALE CACHE EVICTION
        # writer_result entries from before the sentinel parser lack "body".
        # Clear them so the user sees the idle state rather than raw markers.
        # ----------------------------------------------------------------
        elif writer_result and "body" not in writer_result:
            st.session_state.pop("writer_result", None)
            st.info(
                "The article output format was updated. "
                "Please click **Generate SEO Article** again to get structured output."
            )

        # ----------------------------------------------------------------
        # B) RESULT view — shown after generation
        # ----------------------------------------------------------------
        elif writer_result:
            # body_text = clean prose (sentinel-parsed). Falls back to raw markdown for
            # old cached results that pre-date the sentinel system.
            raw_md     = writer_result.get("markdown", "")
            body_text  = writer_result.get("body") or writer_result.get("clean_markdown") or raw_md
            tech_seo   = writer_result.get("tech_seo", "")
            html_text  = writer_result.get("html", "")
            art_kw     = writer_result.get("primary_kw", effective_primary)
            safe_slug  = (art_kw or "article").replace(" ", "_")

            # Output tabs
            tab_visual, tab_seo, tab_html, tab_outline = st.tabs(
                ["Visual", "SEO Package", "</> HTML", "Outline"]
            )

            with tab_visual:
                st.markdown(body_text)

            with tab_seo:
                if tech_seo:
                    st.caption(
                        "Raw Technical SEO package — meta tags, JSON-LD schema, "
                        "Open Graph & Twitter Cards. Copy-paste directly into your CMS `<head>`."
                    )
                    st.code(tech_seo, language="html")
                else:
                    st.info(
                        "No SEO package extracted. "
                        "Re-generate the article to get structured output — "
                        "the model may not have used the sentinel format yet."
                    )

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

            # -- Primary: Save to Library ---------------------------------
            _save_col, _save_status_col = st.columns([1, 3])
            with _save_col:
                _save_clicked = st.button(
                    "💾 Save to Library",
                    type="primary",
                    use_container_width=True,
                    key="tb_save_library",
                )
            with _save_status_col:
                if st.session_state.get("last_saved_article"):
                    st.success(f"Saved: `{st.session_state['last_saved_article']}`")

            if _save_clicked:
                try:
                    import pandas as _pd
                    from datetime import datetime as _dt
                    from V2_Engine.knowledge_base.manager import KnowledgeManager as _KM
                    os.makedirs(_KB_GEO_FOLDER, exist_ok=True)
                    _km = _KM()
                    _fname_base = _km.make_filename(art_kw or "article").replace(".md", "")
                    _meta_df = _pd.DataFrame([{
                        "primary_kw":    art_kw,
                        "saved_at":      _dt.now().strftime("%Y-%m-%d %H:%M"),
                        "word_count":    len(body_text.split()),
                        "model":         model,
                        "content_level": st.session_state.get("w_content_level", ""),
                        "tone":          st.session_state.get("w_tone", ""),
                    }])
                    _saved = _km.save_insight(
                        subfolder="6_seo_writer",
                        filename=_fname_base,
                        content=body_text,
                        dataframe=_meta_df,
                    )
                    st.session_state["last_saved_article"] = _saved
                    st.rerun()
                except Exception as _exc:
                    st.error(f"Save failed: {_exc}")

            row1 = st.columns(4)
            row2 = st.columns(4)

            # Row 1 — Copy / Download
            with row1[0]:
                with st.expander("Copy Markdown"):
                    st.code(body_text, language="markdown")

            with row1[1]:
                with st.expander("Copy HTML"):
                    st.code(html_text, language="html")

            with row1[2]:
                st.download_button(
                    "Download .md",
                    data=body_text,
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
            def _cb_regen():
                st.session_state.pop("writer_result", None)
                st.session_state.pop("last_saved_article", None)

            def _cb_write_another():
                for _k in (
                    "writer_result", "selected_primary_kw",
                    "selected_secondary_kws", "selected_intent",
                    "discovery_shortlist", "last_saved_article",
                ):
                    st.session_state.pop(_k, None)
                st.session_state["geo_nav"] = "Keyword Galaxy"

            def _cb_discover():
                st.session_state["geo_nav"] = "Discovery Grid"

            def _cb_library():
                st.session_state["geo_nav"] = "Output Library"

            with row2[0]:
                st.button("Regenerate", use_container_width=True, key="tb_regen",
                          on_click=_cb_regen)

            with row2[1]:
                st.button("Write Another", use_container_width=True, key="tb_another",
                          on_click=_cb_write_another)

            with row2[2]:
                st.button("Discover More Ideas", use_container_width=True, key="tb_discover",
                          on_click=_cb_discover)

            with row2[3]:
                st.button("Go to Library", use_container_width=True, key="tb_library",
                          on_click=_cb_library)

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
                def _cb_go_galaxy():
                    st.session_state["geo_nav"] = "Keyword Galaxy"

                st.button("Go to Keyword Galaxy", key="writer_go_galaxy",
                          on_click=_cb_go_galaxy)
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
    st.caption("Your generated articles — paired Markdown + CSV metadata (Twin-File Protocol).")

    os.makedirs(_KB_GEO_FOLDER, exist_ok=True)

    md_files = sorted(
        [f for f in os.listdir(_KB_GEO_FOLDER) if f.endswith(".md")],
        reverse=True,
    )

    if not md_files:
        st.info(
            "No articles saved yet.  \n"
            "Generate your first article in the **Writer Engine**, then click **💾 Save to Library**."
        )
        if st.button("Go to Writer Engine", key="lib_go_writer"):
            st.session_state["geo_nav"] = "Writer Engine"
            st.rerun()
        return

    st.subheader(f"Saved Articles ({len(md_files)})")

    import pandas as pd

    # ---- Column header row ----
    hdr = st.columns([4, 2, 2, 1, 1, 1])
    hdr[0].caption("**Keyword / Title**")
    hdr[1].caption("**Saved**")
    hdr[2].caption("**Words**")
    hdr[3].caption("**Size**")
    hdr[4].caption("")
    hdr[5].caption("")

    st.divider()

    for fname in md_files:
        fpath    = os.path.join(_KB_GEO_FOLDER, fname)
        csv_path = fpath.replace(".md", ".csv")
        file_kb  = os.path.getsize(fpath) / 1024

        # Default values parsed from the filename slug
        keyword    = fname.replace(".md", "")
        saved_at   = "—"
        word_count = "—"

        if os.path.exists(csv_path):
            try:
                _meta = pd.read_csv(csv_path)
                if len(_meta) > 0:
                    _row = _meta.iloc[0].to_dict()
                    keyword    = str(_row.get("primary_kw", keyword))
                    saved_at   = str(_row.get("saved_at", "—"))
                    word_count = str(_row.get("word_count", "—"))
            except Exception:
                pass

        is_open  = st.session_state.get("lib_view_file") == fname
        row_cols = st.columns([4, 2, 2, 1, 1, 1])
        row_cols[0].markdown(f"**{keyword}**")
        row_cols[1].caption(saved_at)
        row_cols[2].caption(f"{word_count}w" if word_count != "—" else "—")
        row_cols[3].caption(f"{file_kb:.1f}KB")

        with row_cols[4]:
            if st.button(
                "Close" if is_open else "View",
                key=f"lib_view_{fname}",
                use_container_width=True,
            ):
                if is_open:
                    st.session_state.pop("lib_view_file", None)
                else:
                    st.session_state["lib_view_file"] = fname
                st.rerun()

        with row_cols[5]:
            if st.button(
                "🗑", key=f"lib_del_{fname}",
                use_container_width=True, help="Delete this article",
            ):
                os.remove(fpath)
                if os.path.exists(csv_path):
                    os.remove(csv_path)
                if st.session_state.get("lib_view_file") == fname:
                    st.session_state.pop("lib_view_file", None)
                st.session_state.pop("last_saved_article", None)
                st.rerun()

        # ---- Inline article preview ----
        if is_open:
            with open(fpath, "r", encoding="utf-8") as _f:
                _content = _f.read()
            with st.container(border=True):
                _tab_visual, _tab_md, _tab_dl = st.tabs(["Visual", "Markdown", "Download"])
                with _tab_visual:
                    st.markdown(_content)
                with _tab_md:
                    st.code(_content, language="markdown")
                with _tab_dl:
                    st.download_button(
                        "⬇ Download .md",
                        data=_content,
                        file_name=fname,
                        mime="text/markdown",
                        key=f"lib_dl_{fname}",
                        use_container_width=True,
                    )


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
