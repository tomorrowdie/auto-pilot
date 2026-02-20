"""
Source 3 — Rufus Adversarial Defense Dashboard (Text-Only Mode).

Accepts raw text dumps (paste or .txt upload) for both Part 1 and Part 2.
No image processing or OCR — the LLM parses structure directly.

Robust Mode:
1. Model Routing: Vault model passed to all analyzer calls.
2. Dashboard Gate: Hard stop when 0 agents succeed.
3. Circuit Breaker in analyzer: CPO skipped if <2 agents OK.
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from V2_Engine.processors.source_3_rufus.rufus_analyzer import (
    run_audit_team,
    run_yellow_team,
    run_orange_team,
    aggregate_intelligence,
    generate_strategy_report,
)
from V2_Engine.knowledge_base.manager import KnowledgeManager
from V2_Engine.saas_core.auth import auth_manager

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_KB_FOLDER = "3_rufus_defense"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _read_text_files(files: list) -> str:
    """Read uploaded .txt/.md files and return concatenated text."""
    parts = []
    for f in files:
        try:
            raw = f.read()
            text = raw.decode("utf-8", errors="replace").strip()
            if text:
                parts.append(f"--- [{f.name}] ---\n{text}")
        except Exception as e:
            st.warning(f"Could not read {f.name}: {e}")
    return "\n\n".join(parts)


def _build_master_risk_df(intelligence: dict) -> pd.DataFrame:
    """
    Consolidate ALL risks from Red/Yellow/Orange teams into one DataFrame.

    Columns: Source, Type, Issue, Detail
    Used for both the Risk Radar display and the CSV export.
    """
    rows = []

    # Red Team traps (from trap_questions_archive)
    archive = intelligence.get("trap_questions_archive", {})
    for trap in archive.get("p1_traps", []):
        rows.append({
            "Source": "Red Team (P1 — Rufus Q&A)",
            "Type": trap.get("type", "Unknown"),
            "Issue": trap.get("question", ""),
            "Detail": trap.get("reasoning", ""),
        })
    for trap in archive.get("p2_traps", []):
        rows.append({
            "Source": "Red Team (P2 — Specs/Tags)",
            "Type": trap.get("type", "Unknown"),
            "Issue": trap.get("question", ""),
            "Detail": trap.get("reasoning", ""),
        })

    # Yellow Team dealbreakers + missing info (from customer_reality)
    cr = intelligence.get("customer_reality", {})
    for d in cr.get("dealbreakers", []):
        rows.append({
            "Source": "Yellow (Dealbreaker)",
            "Type": d.get("type", "Customer Issue"),
            "Issue": d.get("issue", ""),
            "Detail": f"Severity: {d.get('severity', '?')} — {d.get('quote', '')}",
        })
    for m in cr.get("missing_info", []):
        rows.append({
            "Source": "Yellow (Missing Info)",
            "Type": m.get("status", "unanswered"),
            "Issue": m.get("question", ""),
            "Detail": f"Risk: {m.get('risk', '')}",
        })

    # Orange Team unaddressed gaps + SEO flags (from listing_gaps)
    lg = intelligence.get("listing_gaps", {})
    for gap in lg.get("unaddressed", []):
        rows.append({
            "Source": "Orange (Listing Gap)",
            "Type": f"Priority: {gap.get('priority', '?')}",
            "Issue": gap.get("issue", ""),
            "Detail": f"Source: {gap.get('source', '')}",
        })
    for flag in lg.get("seo_flags", []):
        rows.append({
            "Source": "Orange (SEO Flag)",
            "Type": f"Severity: {flag.get('severity', '?')}",
            "Issue": flag.get("issue", ""),
            "Detail": f"Risk: {flag.get('risk', '')} — Fix: {flag.get('fix', '')}",
        })

    return pd.DataFrame(rows) if rows else pd.DataFrame()


# ---------------------------------------------------------------------------
# Main render function
# ---------------------------------------------------------------------------
def render_rufus_page():
    st.title("Source 3: Rufus Defense (Adversarial Simulation)")

    # --- 1. Auth Check (V5 Vault) ---
    user_id = st.session_state.get("user_id", "dev_admin")
    if not auth_manager.get_active_providers(user_id):
        st.warning(
            "**System Locked:** Add an API Key in the **API Keys** sidebar "
            "to enable Rufus Analysis."
        )
        return

    # --- 2. Input Section (Text-Only) ---
    tab_p1, tab_p2, tab_p3, tab_p4 = st.tabs([
        "Rufus Chat (The Attack)",
        "Specific Info (The Defense Claims)",
        "Reviews & Q&A (The Battlefield)",
        "Your Listing (The Mirror)",
    ])

    # === TAB 1: Rufus Chat ===
    with tab_p1:
        p1_paste = st.text_area(
            "Paste Rufus Chat History",
            height=300,
            key="p1_paste_input",
            placeholder="Paste the full Rufus Q&A conversation here...",
        )
        p1_files = st.file_uploader(
            "Or upload .txt logs",
            type=["txt", "md"],
            accept_multiple_files=True,
            key="p1_files_input",
        )

    # === TAB 2: Specific Info ===
    with tab_p2:
        p2_paste = st.text_area(
            "Paste 'Specific Info' Q&A Text",
            height=300,
            key="p2_paste_input",
            placeholder="Paste the product-specific info text here...",
        )
        p2_files = st.file_uploader(
            "Or upload .txt logs",
            type=["txt", "md"],
            accept_multiple_files=True,
            key="p2_files_input",
        )

    # === TAB 3: Reviews & Q&A (Yellow Team) ===
    with tab_p3:
        p3_paste = st.text_area(
            "Paste Amazon Reviews & Q&A",
            height=300,
            key="p3_paste_input",
            placeholder=(
                "Paste raw customer reviews and Q&A here...\n"
                "Star ratings are optional — the AI Gatekeeper "
                "classifies by sentiment, not metadata."
            ),
        )
        p3_files = st.file_uploader(
            "Or upload .txt logs",
            type=["txt", "md"],
            accept_multiple_files=True,
            key="p3_files_input",
        )

    # === TAB 4: Your Listing (Orange Team) ===
    with tab_p4:
        p4_title = st.text_input(
            "Amazon Product Title",
            key="p4_title_input",
            placeholder="Paste your current Amazon title here...",
        )
        p4_bullets = st.text_area(
            "Bullet Points",
            height=200,
            key="p4_bullets_input",
            placeholder="Paste your 5 bullet points here...",
        )
        p4_aplus = st.text_area(
            "A+ Content Text (optional)",
            height=150,
            key="p4_aplus_input",
            placeholder=(
                "Paste the text from your A+ Content modules. "
                "Leave blank if images-only."
            ),
        )
        p4_details = st.text_area(
            "Product Details / Specs",
            height=150,
            key="p4_details_input",
            placeholder=(
                "Paste the technical specs here (Dimensions, Weight, "
                "Material, Best Sellers Rank info...)"
            ),
        )
        p4_aplus_status = st.radio(
            "A+ Content Type",
            options=[
                "Standard Text Modules (SEO Friendly)",
                "Images Only / Text embedded in Images (SEO Invisible)",
            ],
            key="p4_aplus_status",
            help=(
                "If your A+ uses only images with text baked in, "
                "crawlers and Rufus cannot read it."
            ),
        )

    # --- 3. Action Section ---
    st.divider()

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        agent_provider, agent_model = auth_manager.render_tab_model_selector(
            user_id, tab_key="rufus_agent", label="Analyst Model (4 agents)",
        )
    with col_m2:
        cpo_provider, cpo_model = auth_manager.render_tab_model_selector(
            user_id, tab_key="rufus_cpo", label="CPO Model (Strategy)",
        )
    agent_api_key = auth_manager.get_api_key(user_id, agent_provider)
    cpo_api_key = auth_manager.get_api_key(user_id, cpo_provider)

    has_input = bool(
        p1_paste.strip() or p1_files or p2_paste.strip() or p2_files
        or p3_paste.strip() or p3_files
        or p4_title.strip() or p4_bullets.strip()
    )

    if st.button(
        "Run Rufus Defense Simulation",
        type="primary",
        disabled=not has_input,
        use_container_width=True,
        key="rufus_run_btn",
    ):
        with st.status("Initializing War Room...", expanded=True) as status:

            # Step A: Concatenate text inputs
            status.update(label="Preparing input text...")

            p1_parts = []
            if p1_paste.strip():
                p1_parts.append(p1_paste.strip())
            if p1_files:
                file_text = _read_text_files(p1_files)
                if file_text:
                    p1_parts.append(file_text)
            text_part_1 = "\n\n".join(p1_parts)

            p2_parts = []
            if p2_paste.strip():
                p2_parts.append(p2_paste.strip())
            if p2_files:
                file_text = _read_text_files(p2_files)
                if file_text:
                    p2_parts.append(file_text)
            text_part_2 = "\n\n".join(p2_parts)

            p3_parts = []
            if p3_paste.strip():
                p3_parts.append(p3_paste.strip())
            if p3_files:
                file_text = _read_text_files(p3_files)
                if file_text:
                    p3_parts.append(file_text)
            text_part_3 = "\n\n".join(p3_parts)

            # Step B: Validate
            p1_words = len(text_part_1.split()) if text_part_1.strip() else 0
            p2_words = len(text_part_2.split()) if text_part_2.strip() else 0
            p3_words = len(text_part_3.split()) if text_part_3.strip() else 0

            if p1_words == 0 and p2_words == 0 and p3_words == 0:
                status.update(
                    label="No data provided", state="error", expanded=True,
                )
                st.error("All inputs are empty. Paste text or upload files.")
                return

            if p1_words == 0:
                st.warning(
                    "Part 1 (Rufus Chat) is empty. "
                    "Red/Blue agents for user context will be skipped."
                )
            if p2_words == 0:
                st.warning(
                    "Part 2 (Specific Info) is empty. "
                    "Spec analysis agents will be skipped."
                )
            if p3_words == 0:
                st.info(
                    "Part 3 (Reviews & Q&A) is empty. "
                    "Yellow Team will be skipped."
                )

            st.caption(
                f"Input: Part 1 = {p1_words} words, "
                f"Part 2 = {p2_words} words, "
                f"Part 3 = {p3_words} words"
            )

            # Step C: Red/Blue Team (4 agents)
            status.update(
                label="Red Team & Blue Team are analyzing gaps...",
            )
            team_results = run_audit_team(
                text_part_1, text_part_2,
                provider=agent_provider,
                api_key=agent_api_key,
                model=agent_model,
            )

            stats = team_results.get("stats", {})
            agents_ok = stats.get("agents_ok", 0)
            agents_error = stats.get("agents_error", 0)

            if agents_error > 0:
                st.warning(
                    f"Audit team: {agents_ok} OK, "
                    f"{agents_error} errors"
                )

            # --- Dashboard Gate: Hard stop on total failure ---
            if agents_ok == 0 and stats.get("agents_run", 0) > 0:
                status.update(
                    label="Critical Failure — All agents crashed",
                    state="error",
                    expanded=True,
                )
                st.error(
                    "All agents returned errors. "
                    "The CPO cannot build a strategy from empty data.\n\n"
                    "**Check:** API Key valid? Input text not empty?"
                )
                st.session_state["rufus_results"] = team_results
                st.session_state["rufus_intelligence"] = {}
                st.session_state["rufus_cpo_report"] = ""
                st.session_state["rufus_master_df"] = pd.DataFrame()
                return

            # Step D: Yellow Team (Reviews & Q&A) — optional
            if text_part_3.strip():
                status.update(
                    label="Yellow Team: Classifying reviews...",
                )
                try:
                    yellow_results = run_yellow_team(
                        text_part_3,
                        provider=agent_provider,
                        api_key=agent_api_key,
                        model=agent_model,
                    )
                    team_results["yellow"] = yellow_results

                    y_stats = yellow_results.get("stats", {})
                    y_ok = y_stats.get("agents_ok", 0)
                    y_err = y_stats.get("agents_error", 0)
                    if y_err > 0:
                        st.warning(
                            f"Yellow Team: {y_ok} OK, {y_err} errors"
                        )
                except Exception as e:
                    st.error(f"Yellow Team failed: {e}")

            # Step E: Orange Team (Listing Gap Analysis) — optional
            has_listing = bool(p4_title.strip() or p4_bullets.strip())
            if has_listing:
                status.update(
                    label="Orange Team: Analyzing listing gaps...",
                )
                try:
                    orange_results = run_orange_team(
                        listing_title=p4_title.strip(),
                        listing_bullets=p4_bullets.strip(),
                        listing_aplus=p4_aplus.strip(),
                        product_details=p4_details.strip(),
                        aplus_status=p4_aplus_status,
                        team_results=team_results,
                        provider=agent_provider,
                        api_key=agent_api_key,
                        model=agent_model,
                    )
                    team_results["orange"] = orange_results

                    o_stats = orange_results.get("stats", {})
                    o_ok = o_stats.get("agents_ok", 0)
                    o_err = o_stats.get("agents_error", 0)
                    if o_err > 0:
                        st.warning(
                            f"Orange Team: {o_ok} OK, {o_err} errors"
                        )
                except Exception as e:
                    st.error(f"Orange Team failed: {e}")

            # Step F: CPO Synthesis
            status.update(
                label=f"CPO (Master Strategist) drafting on {cpo_model}...",
            )
            cpo_report = ""
            try:
                cpo_report = generate_strategy_report(
                    team_results,
                    provider=cpo_provider,
                    api_key=cpo_api_key,
                    model=cpo_model,
                )
            except Exception as e:
                st.error(f"CPO report failed: {e}")
                cpo_report = f"# CPO Report Error\n\n{e}"

            # Store results
            st.session_state["rufus_results"] = team_results
            st.session_state["rufus_intelligence"] = aggregate_intelligence(
                team_results,
            )
            st.session_state["rufus_cpo_report"] = cpo_report
            st.session_state["rufus_master_df"] = _build_master_risk_df(
                st.session_state["rufus_intelligence"],
            )

            status.update(
                label="Simulation Complete!",
                state="complete",
                expanded=False,
            )

    # --- 4. Results Display (Hybrid Design) ---
    results = st.session_state.get("rufus_results")
    if not results:
        return

    intelligence = st.session_state.get("rufus_intelligence", {})
    cpo_report = st.session_state.get("rufus_cpo_report", "")
    master_df = st.session_state.get("rufus_master_df", pd.DataFrame())

    st.divider()
    st.subheader("Strategic Analysis")

    rt_war, rt_radar, rt_yellow, rt_orange, rt_cpo, rt_raw = st.tabs([
        "War Room (Red/Blue)",
        "Risk Radar",
        "Friction Shield (Yellow)",
        "Listing Gaps (Orange)",
        "CPO Strategy",
        "Raw Data",
    ])

    # -----------------------------------------------------------------
    # TAB 1: WAR ROOM (Qualitative)
    # -----------------------------------------------------------------
    with rt_war:
        col_red, col_blue = st.columns(2)

        # --- RED TEAM ---
        with col_red:
            st.error("**RED TEAM (Gaps & Risks)**")

            with st.expander("Part 1: Chat Traps", expanded=True):
                p1_audit = results.get("p1_audit", {})
                if "_error" in p1_audit:
                    st.markdown(f"Agent error: {p1_audit['_error']}")
                elif "_skipped" in p1_audit:
                    st.markdown(p1_audit["_skipped"])
                else:
                    report = p1_audit.get("auditor_report", {})
                    weakness = report.get("weakness_found", "")
                    if weakness:
                        st.markdown(f"**Weakness:** {weakness}")
                    for trap in report.get("trap_questions", []):
                        st.markdown(
                            f"- **{trap.get('type', 'Trap')}:** "
                            f"{trap.get('question', '')}\n"
                            f"  > _{trap.get('reasoning', '')}_"
                        )

            with st.expander("Part 2: Info Gaps", expanded=True):
                p2_audit = results.get("p2_audit", {})
                if "_error" in p2_audit:
                    st.markdown(f"Agent error: {p2_audit['_error']}")
                elif "_skipped" in p2_audit:
                    st.markdown(p2_audit["_skipped"])
                else:
                    report = p2_audit.get("auditor_report", {})
                    weakness = report.get("weakness_found", "")
                    if weakness:
                        st.markdown(f"**Weakness:** {weakness}")
                    for trap in report.get("trap_questions", []):
                        st.markdown(
                            f"- **{trap.get('type', 'Trap')}:** "
                            f"{trap.get('question', '')}\n"
                            f"  > _{trap.get('reasoning', '')}_"
                        )

        # --- BLUE TEAM ---
        with col_blue:
            st.info("**BLUE TEAM (Hooks & Assets)**")

            with st.expander("Part 1: Customer Psychology", expanded=True):
                p1_insight = results.get("p1_insight", {})
                if "_error" in p1_insight:
                    st.markdown(f"Agent error: {p1_insight['_error']}")
                elif "_skipped" in p1_insight:
                    st.markdown(p1_insight["_skipped"])
                else:
                    pi = p1_insight.get("product_insight", {})
                    persona = pi.get("customer_profile", "")
                    desire = pi.get("key_desire", "")
                    fear = pi.get("key_fear", "")
                    if persona:
                        st.markdown(f"**Persona:** {persona}")
                    if desire:
                        st.markdown(f"**Desire:** {desire}")
                    if fear:
                        st.markdown(f"**Fear:** {fear}")
                    for vq in pi.get("validation_questions", []):
                        st.markdown(
                            f"- **{vq.get('type', 'Q')}:** "
                            f"{vq.get('question', '')}\n"
                            f"  > _{vq.get('insight_origin', '')}_"
                        )

            with st.expander("Part 2: Brand Identity", expanded=True):
                p2_insight = results.get("p2_insight", {})
                if "_error" in p2_insight:
                    st.markdown(f"Agent error: {p2_insight['_error']}")
                elif "_skipped" in p2_insight:
                    st.markdown(p2_insight["_skipped"])
                else:
                    mi = p2_insight.get("marketing_insight", {})
                    identity = mi.get("core_identity", "")
                    selling = mi.get("key_selling_point", "")
                    if identity:
                        st.markdown(f"**Identity:** {identity}")
                    if selling:
                        st.markdown(f"**Selling Point:** {selling}")
                    for cq in mi.get("confirmation_questions", []):
                        st.markdown(
                            f"- **{cq.get('type', 'Q')}:** "
                            f"{cq.get('question', '')}\n"
                            f"  > _{cq.get('insight_origin', '')}_"
                        )

    # -----------------------------------------------------------------
    # TAB 2: RISK RADAR (Quantitative)
    # -----------------------------------------------------------------
    with rt_radar:
        st.caption("Risk visualization across all teams (Red/Yellow/Orange).")

        if not master_df.empty:
            st.markdown("### Risk Categories")
            type_counts = (
                master_df.groupby("Type", as_index=False)
                .size()
                .rename(columns={"size": "count"})
                .sort_values("count", ascending=False)
            )
            if not type_counts.empty:
                st.bar_chart(type_counts.set_index("Type")["count"])

            col_total, col_red, col_yellow, col_orange = st.columns(4)
            with col_total:
                st.metric("Total Risks", len(master_df))
            with col_red:
                red_count = len(
                    master_df[master_df["Source"].str.contains("Red")]
                )
                st.metric("Red Team", red_count)
            with col_yellow:
                yellow_count = len(
                    master_df[master_df["Source"].str.contains("Yellow")]
                )
                st.metric("Yellow Team", yellow_count)
            with col_orange:
                orange_count = len(
                    master_df[master_df["Source"].str.contains("Orange")]
                )
                st.metric("Orange Team", orange_count)

            st.divider()
            st.markdown("### Full Risk Register")
            st.dataframe(
                master_df,
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No risks detected across any team.")

        tags = results.get("tags", [])
        if tags:
            st.divider()
            st.markdown("### Extracted Tags")
            st.write(", ".join(f"`{t}`" for t in tags))

    # -----------------------------------------------------------------
    # TAB 3: FRICTION SHIELD (Yellow Team)
    # -----------------------------------------------------------------
    with rt_yellow:
        yellow_data = results.get("yellow")
        if not yellow_data:
            st.info(
                "Yellow Team did not run. "
                "Paste Reviews & Q&A in the 3rd input tab to activate."
            )
        else:
            # Gatekeeper Stats
            gk = yellow_data.get("gatekeeper", {})
            if "_error" in gk:
                st.error(f"Gatekeeper failed: {gk['_error']}")
            else:
                gk_data = gk.get("gatekeeper", {})
                col_pos, col_neg = st.columns(2)
                with col_pos:
                    st.metric(
                        "Positive Reviews",
                        gk_data.get("positive_count", "?"),
                    )
                with col_neg:
                    st.metric(
                        "Negative Reviews",
                        gk_data.get("negative_count", "?"),
                    )

            st.divider()

            # Hero Scenarios
            st.markdown("### Hero Scenarios (Positive Auditor)")
            heroes = yellow_data.get("hero_scenarios", {})
            if "_error" in heroes:
                st.warning(f"Agent error: {heroes['_error']}")
            elif "_skipped" in heroes:
                st.info(heroes["_skipped"])
            else:
                hero_list = heroes.get("hero_scenarios", [])
                if hero_list:
                    hero_rows = []
                    for h in hero_list:
                        hero_rows.append({
                            "Occasion": h.get("occasion", ""),
                            "Emotion": h.get("emotion", ""),
                            "COSMO Intent": h.get("cosmo_intent", ""),
                            "Quote": h.get("quote", ""),
                        })
                    st.dataframe(
                        pd.DataFrame(hero_rows),
                        use_container_width=True,
                        hide_index=True,
                    )
                else:
                    st.info("No hero scenarios extracted.")

            st.divider()

            # Dealbreakers
            st.markdown("### Dealbreakers (Negative Auditor)")
            deals = yellow_data.get("dealbreakers", {})
            if "_error" in deals:
                st.warning(f"Agent error: {deals['_error']}")
            elif "_skipped" in deals:
                st.info(deals["_skipped"])
            else:
                deal_list = deals.get("dealbreakers", [])
                if deal_list:
                    deal_rows = []
                    for d in deal_list:
                        deal_rows.append({
                            "Type": d.get("type", ""),
                            "Issue": d.get("issue", ""),
                            "Severity": d.get("severity", ""),
                            "Quote": d.get("quote", ""),
                        })
                    st.dataframe(
                        pd.DataFrame(deal_rows),
                        use_container_width=True,
                        hide_index=True,
                    )
                else:
                    st.info("No dealbreakers found.")

                # Missing Info
                missing = deals.get("missing_info", [])
                if missing:
                    st.markdown("### Missing Info (Unanswered Questions)")
                    missing_rows = []
                    for m in missing:
                        missing_rows.append({
                            "Question": m.get("question", ""),
                            "Status": m.get("status", ""),
                            "Risk": m.get("risk", ""),
                        })
                    st.dataframe(
                        pd.DataFrame(missing_rows),
                        use_container_width=True,
                        hide_index=True,
                    )

    # -----------------------------------------------------------------
    # TAB 4: LISTING GAPS (Orange Team)
    # -----------------------------------------------------------------
    with rt_orange:
        orange_data = results.get("orange")
        if not orange_data:
            st.info(
                "Orange Team did not run. "
                "Paste your Listing (Title & Bullets) in the 4th input tab "
                "to activate Gap Analysis."
            )
        else:
            gap_raw = orange_data.get("gap_analysis", {})
            if "_error" in gap_raw:
                st.error(f"Orange Team failed: {gap_raw['_error']}")
            else:
                ga = gap_raw.get("gap_analysis", {})

                # Coverage Score
                score = ga.get("coverage_score", "?")
                st.metric("Listing Coverage Score", f"{score} / 10")

                st.divider()

                # Addressed issues
                addressed = ga.get("addressed", [])
                if addressed:
                    st.markdown("### Addressed (Listing Handles These)")
                    addr_rows = []
                    for a in addressed:
                        addr_rows.append({
                            "Issue": a.get("issue", ""),
                            "Listing Evidence": a.get("listing_evidence", ""),
                        })
                    st.dataframe(
                        pd.DataFrame(addr_rows),
                        use_container_width=True,
                        hide_index=True,
                    )

                # Unaddressed gaps
                unaddressed = ga.get("unaddressed", [])
                if unaddressed:
                    st.markdown("### Unaddressed Gaps (Listing Ignores These)")
                    gap_rows = []
                    for u in unaddressed:
                        gap_rows.append({
                            "Issue": u.get("issue", ""),
                            "Source": u.get("source", ""),
                            "Priority": u.get("priority", ""),
                        })
                    st.dataframe(
                        pd.DataFrame(gap_rows),
                        use_container_width=True,
                        hide_index=True,
                    )

                st.divider()

                # Fix Suggestions
                fixes = ga.get("fix_suggestions", [])
                if fixes:
                    st.markdown("### Fix Suggestions (Rewrites)")
                    fix_rows = []
                    for f in fixes:
                        fix_rows.append({
                            "Target": f.get("target", ""),
                            "Problem": f.get("problem", ""),
                            "Suggested Fix": f.get("fix", ""),
                        })
                    st.dataframe(
                        pd.DataFrame(fix_rows),
                        use_container_width=True,
                        hide_index=True,
                    )

                # SEO Flags
                seo_flags = ga.get("seo_flags", [])
                if seo_flags:
                    st.divider()
                    st.markdown("### SEO Flags")
                    for flag in seo_flags:
                        severity = flag.get("severity", "warning")
                        msg = (
                            f"**{flag.get('issue', '')}**\n\n"
                            f"Risk: {flag.get('risk', '')}\n\n"
                            f"Fix: {flag.get('fix', '')}"
                        )
                        if severity == "critical":
                            st.error(msg)
                        else:
                            st.warning(msg)

    # -----------------------------------------------------------------
    # TAB 5: CPO STRATEGY (Final Output)
    # -----------------------------------------------------------------
    with rt_cpo:
        if cpo_report:
            st.markdown(cpo_report)
        else:
            st.info("CPO Strategy Report not available.")

        st.divider()
        project_name = st.text_input(
            "Project Name for Save",
            value="Rufus_Defense_01",
            key="rufus_project_name",
        )
        if st.button("Save Defense Strategy", key="rufus_save_kb"):
            kb = KnowledgeManager()
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            filename = kb.make_filename(project_name.strip())

            tc = intelligence.get("target_customer", {})
            ma = intelligence.get("marketing_assets", {})
            archive = intelligence.get("trap_questions_archive", {})
            cr = intelligence.get("customer_reality", {})
            lg = intelligence.get("listing_gaps", {})

            # ── HEADER ──────────────────────────────────────────
            md_lines = [
                f"# Rufus Defense Dossier: {project_name.strip()}",
                "",
                f"**Generated:** {now}",
                f"**Agents Run:** {results['stats']['agents_run']}",
                f"**Agents OK:** {results['stats']['agents_ok']}",
                "",
                "---",
                "",
            ]

            # ── SECTION 1: Intelligence Summary ─────────────────
            md_lines.extend([
                "## 1. Intelligence Summary",
                "",
                f"| Field | Value |",
                f"|-------|-------|",
                f"| **Persona** | {tc.get('persona', 'N/A')} |",
                f"| **Desire** | {tc.get('desire', 'N/A')} |",
                f"| **Fear** | {tc.get('fear', 'N/A')} |",
                f"| **Identity** | {ma.get('identity', 'N/A')} |",
                f"| **Selling Point** | {ma.get('selling_point', 'N/A')} |",
                "",
            ])

            risks = intelligence.get("product_risks", [])
            if risks:
                md_lines.append("### All Product Risks")
                md_lines.append("")
                for r in risks:
                    md_lines.append(f"- {r}")
                md_lines.append("")

            md_lines.extend(["---", ""])

            # ── SECTION 2: War Room (Red/Blue) ──────────────────
            md_lines.extend([
                "## 2. War Room (Red/Blue Team)",
                "",
            ])

            p1_traps = archive.get("p1_traps", [])
            p2_traps = archive.get("p2_traps", [])
            if p1_traps or p2_traps:
                md_lines.extend([
                    "### Trap Questions (Auditor Findings)",
                    "",
                    "| Source | Type | Question | Reasoning |",
                    "|--------|------|----------|-----------|",
                ])
                for t in p1_traps:
                    md_lines.append(
                        f"| P1 — Rufus Q&A | {t.get('type', '')} "
                        f"| {t.get('question', '')} "
                        f"| {t.get('reasoning', '')} |"
                    )
                for t in p2_traps:
                    md_lines.append(
                        f"| P2 — Specs/Tags | {t.get('type', '')} "
                        f"| {t.get('question', '')} "
                        f"| {t.get('reasoning', '')} |"
                    )
                md_lines.append("")
            else:
                md_lines.extend([
                    "*No trap questions detected by Red Team.*",
                    "",
                ])

            # Validation questions (from analyst insight)
            val_qs = []
            for key in ("p1_insight", "p2_insight"):
                insight = results.get(key, {})
                if "_error" not in insight:
                    ar = insight.get("analyst_report", {})
                    val_qs.extend(ar.get("critical_questions", []))
            if val_qs:
                md_lines.extend([
                    "### Validation Questions (Analyst Findings)",
                    "",
                ])
                for cq in val_qs:
                    q = cq.get("question", "")
                    origin = cq.get("insight_origin", "")
                    md_lines.append(f"- **{q}**  _{origin}_")
                md_lines.append("")

            md_lines.extend(["---", ""])

            # ── SECTION 3: Friction Shield (Yellow) ─────────────
            md_lines.extend([
                "## 3. Friction Shield (Yellow Team)",
                "",
            ])

            heroes = cr.get("hero_scenarios", [])
            if heroes:
                md_lines.extend([
                    "### Hero Scenarios (Positive Reviews)",
                    "",
                    "| Occasion | Emotion | COSMO Intent |",
                    "|----------|---------|-------------|",
                ])
                for h in heroes:
                    md_lines.append(
                        f"| {h.get('occasion', '')} "
                        f"| {h.get('emotion', '')} "
                        f"| {h.get('cosmo_intent', '')} |"
                    )
                md_lines.append("")

            dealbreakers = cr.get("dealbreakers", [])
            if dealbreakers:
                md_lines.extend([
                    "### Dealbreakers (Negative Reviews)",
                    "",
                    "| Severity | Issue | Quote |",
                    "|----------|-------|-------|",
                ])
                for d in dealbreakers:
                    md_lines.append(
                        f"| {d.get('severity', '?')} "
                        f"| {d.get('issue', '')} "
                        f"| {d.get('quote', '')} |"
                    )
                md_lines.append("")

            missing = cr.get("missing_info", [])
            if missing:
                md_lines.extend([
                    "### Missing Info (Unanswered Questions)",
                    "",
                    "| Question | Status | Risk |",
                    "|----------|--------|------|",
                ])
                for m in missing:
                    md_lines.append(
                        f"| {m.get('question', '')} "
                        f"| {m.get('status', '?')} "
                        f"| {m.get('risk', '')} |"
                    )
                md_lines.append("")

            if not heroes and not dealbreakers and not missing:
                md_lines.extend([
                    "*Yellow Team did not run (no review data provided).*",
                    "",
                ])

            md_lines.extend(["---", ""])

            # ── SECTION 4: Listing Gaps (Orange) ────────────────
            md_lines.extend([
                "## 4. Listing Gaps (Orange Team)",
                "",
            ])

            if lg:
                score = lg.get("coverage_score", "?")
                md_lines.extend([
                    f"**Listing Coverage Score:** {score} / 10",
                    "",
                ])

                unaddressed = lg.get("unaddressed", [])
                if unaddressed:
                    md_lines.extend([
                        "### Unaddressed Gaps",
                        "",
                        "| Priority | Issue | Source |",
                        "|----------|-------|--------|",
                    ])
                    for gap in unaddressed:
                        md_lines.append(
                            f"| {gap.get('priority', '?')} "
                            f"| {gap.get('issue', '')} "
                            f"| {gap.get('source', '')} |"
                        )
                    md_lines.append("")

                fixes = lg.get("fix_suggestions", [])
                if fixes:
                    md_lines.extend([
                        "### Fix Suggestions",
                        "",
                        "| Target | Problem | Suggested Fix |",
                        "|--------|---------|---------------|",
                    ])
                    for f in fixes:
                        md_lines.append(
                            f"| {f.get('target', '')} "
                            f"| {f.get('problem', '')} "
                            f"| {f.get('fix', '')} |"
                        )
                    md_lines.append("")

                seo_flags = lg.get("seo_flags", [])
                if seo_flags:
                    md_lines.extend([
                        "### SEO Flags",
                        "",
                        "| Severity | Issue | Risk | Fix |",
                        "|----------|-------|------|-----|",
                    ])
                    for flag in seo_flags:
                        md_lines.append(
                            f"| {flag.get('severity', '?')} "
                            f"| {flag.get('issue', '')} "
                            f"| {flag.get('risk', '')} "
                            f"| {flag.get('fix', '')} |"
                        )
                    md_lines.append("")
            else:
                md_lines.extend([
                    "*Orange Team did not run (no listing data provided).*",
                    "",
                ])

            md_lines.extend(["---", ""])

            # ── SECTION 5: CPO Strategy ─────────────────────────
            md_lines.extend([
                "## 5. CPO Strategy Report",
                "",
            ])
            if cpo_report:
                md_lines.extend([cpo_report, ""])
            else:
                md_lines.extend([
                    "*CPO Strategy Report not available.*",
                    "",
                ])

            md_content = "\n".join(md_lines)
            csv_df = master_df if not master_df.empty else None

            kb.save_insight(
                _KB_FOLDER, filename, md_content,
                dataframe=csv_df,
            )
            csv_name = filename.replace(".md", ".csv")
            saved = f"`{_KB_FOLDER}/{filename}`"
            if csv_df is not None:
                saved += f" + `{csv_name}`"
            st.success(f"Full Dossier Saved! {saved}")

    # -----------------------------------------------------------------
    # TAB 6: RAW DATA
    # -----------------------------------------------------------------
    with rt_raw:
        st.markdown("### Aggregated Intelligence")
        st.json(intelligence)

        st.divider()
        st.markdown("### Agent Stats")
        st.json(results.get("stats", {}))

        st.divider()
        st.markdown("### Full Agent Outputs")
        with st.expander("Part 1 Audit (Red)", expanded=False):
            st.json(results.get("p1_audit", {}))
        with st.expander("Part 1 Insight (Blue)", expanded=False):
            st.json(results.get("p1_insight", {}))
        with st.expander("Part 2 Audit (Red)", expanded=False):
            st.json(results.get("p2_audit", {}))
        with st.expander("Part 2 Insight (Blue)", expanded=False):
            st.json(results.get("p2_insight", {}))

        yellow_raw = results.get("yellow")
        if yellow_raw:
            st.divider()
            st.markdown("### Yellow Team Outputs")
            with st.expander("Gatekeeper (Classifier)", expanded=False):
                st.json(yellow_raw.get("gatekeeper", {}))
            with st.expander("Hero Scenarios (Positive)", expanded=False):
                st.json(yellow_raw.get("hero_scenarios", {}))
            with st.expander("Dealbreakers (Negative)", expanded=False):
                st.json(yellow_raw.get("dealbreakers", {}))

        orange_raw = results.get("orange")
        if orange_raw:
            st.divider()
            st.markdown("### Orange Team Outputs")
            with st.expander("Gap Analysis", expanded=False):
                st.json(orange_raw.get("gap_analysis", {}))
