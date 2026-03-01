"""
Top Status Bar — persistent UI component rendered at the top of every main-panel page.

Layout (top → bottom):
    ### 🟢 Active: {project_name}          ← always visible header
    [st.selectbox top_bar_project_selector] ← project switcher
    ⚙️ Manage Project & Data Sources (expander, expanded=True)
        ├── render_webmaster_auth()          ← GSC/Bing — always inside expander
        ├── ✅ Data Sources Connected badge
        ├── ─── divider ───
        ├── New Project Name + [Create] button
        ├── ─── divider ─── (when active project)
        └── #### ⚙️ Project Management tabs
               ├── ✏️ Rename Project
               └── ⚠️ Danger Zone

on_change pattern (key fix):
    _on_project_change() callback fires BEFORE the next rerun.
    It reads st.session_state["top_bar_project_selector"] (already updated),
    looks up the project in the pre-stored _tb_projects list, and writes
    project_id / project_name / project_slug to session_state.
    This ensures the header reads the CORRECT name on the very next rerun.

Dynamic widget keys:
    Rename input uses key=f"tb_rename_{project_id}" — a unique key per
    project.  When the project switches, the key changes → Streamlit creates
    a fresh widget → value=_current_label is honoured (no stale-cache bug).
    Delete button uses disabled=not _confirmed instead of if _confirmed: so
    the button is always visible but only clickable after the checkbox.

Called from app.py via:
    from V2_Engine.dashboard.components.top_bar import render_top_bar
    render_top_bar(db, user_id)
"""

import streamlit as st

from V2_Engine.knowledge_base.manager import KnowledgeManager, slugify_project_name


def render_top_bar(db, user_id: str) -> str | None:
    """
    Render the persistent top status bar.

    Args:
        db:      Database instance (already initialised by app.py)
        user_id: Current user ID (from st.session_state["user_id"])

    Returns:
        active_project_id (str) if a project is selected, else None.

    Side-effects:
        Sets st.session_state["project_id"], ["project_name"], ["project_slug"].
        Calls render_webmaster_auth() which sets ["_webmaster_db"],
        runs the OAuth redirect trap, and pre-warms GSC/Bing site caches.
    """
    # Ensure webmaster_page.py can always resolve the DB without a separate init
    st.session_state.setdefault("_webmaster_db", db)

    _projects = db.get_projects(user_id, "amazon")
    _project_labels = [p["label"] or p["site_url"] for p in _projects]
    _has_projects = bool(_project_labels)

    # Store in session_state so the on_change callback can access them
    # without needing a DB call (callbacks have no direct access to local vars)
    st.session_state["_tb_projects"] = _projects
    st.session_state["_tb_labels"]   = _project_labels

    # ------------------------------------------------------------------
    # ACTIVE PROJECT HEADER — reads from session_state so it reflects
    # the callback's write on the very same rerun (no one-render lag)
    # ------------------------------------------------------------------
    _active_name = st.session_state.get("project_name")
    if _active_name:
        st.markdown(f"### 🟢 Active: **{_active_name}**")
    elif not _has_projects:
        st.caption("No projects yet — create one below.")

    # ------------------------------------------------------------------
    # PROJECT SWITCHER
    # on_change writes project_id/name/slug BEFORE the rerun so every
    # widget below (header, CRUD tabs) sees the new project immediately.
    # ------------------------------------------------------------------
    _active_project: dict | None = None

    if _has_projects:

        def _on_project_change():
            """
            Fires before the rerun that follows a selectbox interaction.
            Writes the full project context to session_state so the header
            and CRUD tabs never show stale data.
            """
            _new_label = st.session_state.get("top_bar_project_selector")
            _labels    = st.session_state.get("_tb_labels", [])
            _projs     = st.session_state.get("_tb_projects", [])
            if _new_label and _new_label in _labels:
                _idx = _labels.index(_new_label)
                _proj = _projs[_idx]
                st.session_state["project_id"]   = _proj["id"]
                st.session_state["project_name"] = _new_label
                st.session_state["project_slug"] = slugify_project_name(_new_label)
            # Wipe stale CRUD widget keys so value= defaults take effect
            st.session_state.pop("tb_rename_to",     None)
            st.session_state.pop("tb_confirm_delete", None)

        _selected_label = st.selectbox(
            "Active Project",
            options=_project_labels,
            key="top_bar_project_selector",
            label_visibility="collapsed",
            on_change=_on_project_change,
        )
        _sel_idx = _project_labels.index(_selected_label)
        _active_project = _projects[_sel_idx]

        # Render-time fallback write: covers the very first render (callback
        # hasn't fired yet) and ensures state is always consistent.
        st.session_state["project_id"]   = _active_project["id"]
        st.session_state["project_name"] = _selected_label
        st.session_state["project_slug"] = slugify_project_name(_selected_label)

    # ------------------------------------------------------------------
    # MANAGE PROJECT & DATA SOURCES — expander
    # expanded=True so auth is always visible on load / project selection
    # ------------------------------------------------------------------
    _google_ok = bool(st.session_state.get("google_sites"))
    _bing_ok   = bool(st.session_state.get("bing_sites"))
    _badge = " ●" if (_google_ok or _bing_ok) else ""

    with st.expander(
        f"⚙️ Manage Project & Data Sources{_badge}",
        expanded=True,
    ):
        # ── Auth — always inside expander, never behind a condition ────
        from V2_Engine.dashboard.webmaster_page import render_webmaster_auth
        render_webmaster_auth(db=db, user_id=user_id)

        # Re-read after pre-warm
        _google_ok = bool(st.session_state.get("google_sites"))
        _bing_ok   = bool(st.session_state.get("bing_sites"))
        if _google_ok or _bing_ok:
            _live = " + ".join(
                (["GSC"] if _google_ok else []) +
                (["Bing"] if _bing_ok else [])
            )
            st.success(f"✅ Data Sources Connected: {_live}")

        st.divider()

        # ── Create new project ────────────────────────────────────────
        _proj_name = st.text_input(
            "New Project Name",
            placeholder="e.g. Garlic Press Launch",
            key="new_proj_name",
        )
        if st.button("Create Project", key="btn_create_project", use_container_width=True):
            if _proj_name.strip():
                db.add_project(user_id, "amazon", _proj_name.strip(), _proj_name.strip())
                st.session_state["project_name"] = _proj_name.strip()
                st.toast(f"Created: {_proj_name.strip()}", icon="✅")
                st.rerun()
            else:
                st.warning("Enter a project name.")

        # ── Rename + Delete (only when a project is active) ───────────
        if _active_project:
            st.divider()
            _render_project_crud(db, _active_project)

    return st.session_state.get("project_id")


# ---------------------------------------------------------------------------
# PRIVATE — Project CRUD (rename + delete)
# ---------------------------------------------------------------------------

def _render_project_crud(db, active_project: dict):
    """
    Render Rename and Delete tabs for the active project.

    Reads all display values from st.session_state["project_name"] /
    ["project_slug"] so the tabs are always in sync with the selectbox —
    never stuck on a stale local variable.
    """
    _km = KnowledgeManager()

    # Always read from session_state — updated by callback before this runs
    _current_label = st.session_state.get("project_name", "")
    _current_slug  = st.session_state.get("project_slug") or slugify_project_name(_current_label)
    _project_id    = active_project["id"]

    st.markdown("#### ⚙️ Project Management")
    tab_rename, tab_delete = st.tabs(["✏️ Rename Project", "⚠️ Danger Zone"])

    # ── Rename tab ─────────────────────────────────────────────────────
    with tab_rename:
        # Dynamic key = fresh widget per project.  When the project changes,
        # _project_id changes → new key → Streamlit treats it as a brand-new
        # widget and honours value=_current_label (no stale-cache problem).
        _rename_val = st.text_input(
            f"New name for: {_current_label}",
            value=_current_label,
            key=f"tb_rename_{_project_id}",
            placeholder="New project name",
        )
        if st.button("Save Name", key="btn_rename_project", use_container_width=True):
            _new_name = _rename_val.strip()
            if not _new_name:
                st.warning("Enter a name.")
            elif _new_name == _current_label:
                st.info("Name unchanged.")
            else:
                _new_slug = slugify_project_name(_new_name)
                db.rename_project_label(_project_id, _new_name)
                _km.rename_project_folder(_current_slug, _new_slug)
                st.session_state["project_name"] = _new_name
                st.session_state["project_slug"] = _new_slug
                # Clear the selectbox key so it repopulates with new label
                st.session_state.pop("top_bar_project_selector", None)
                st.toast(f"Renamed to: {_new_name}", icon="✏️")
                st.rerun()

    # ── Danger Zone tab ────────────────────────────────────────────────
    with tab_delete:
        st.error(
            f"**Delete project: {_current_label}**\n\n"
            "⚠️ This permanently removes the project and all saved files from disk. "
            "This action cannot be undone and backups cannot be recovered."
        )
        _confirmed = st.checkbox(
            "I understand this is irreversible",
            key="tb_confirm_delete",
        )
        # Button always visible — disabled until checkbox is ticked.
        # This ensures the user can always SEE the button and understands
        # they need to confirm first (better UX than hiding it entirely).
        if st.button(
            "🗑️ Delete Project",
            key="btn_delete_project",
            type="primary",
            use_container_width=True,
            disabled=not _confirmed,
        ):
            db.delete_project_by_id(_project_id)
            _km.delete_project_folder(_current_slug)
            for _k in ["project_id", "project_name", "project_slug",
                       "top_bar_project_selector", "tb_confirm_delete"]:
                st.session_state.pop(_k, None)
            st.toast(f"Deleted: {_current_label}", icon="🗑️")
            st.rerun()
