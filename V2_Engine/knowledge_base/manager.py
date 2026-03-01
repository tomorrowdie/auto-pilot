"""
Knowledge Manager — The shared Hub for all data sources.

Generic file/folder CRUD for Markdown insights.
This module has ZERO knowledge of any specific data source (H10, Cerebro, etc.).
Data sources convert their output into Markdown BEFORE calling save_insight().

Twin-File Protocol (Mandatory Standard):
    Every save_insight() call SHOULD include a dataframe parameter.
    This produces a paired MD + CSV output for full traceability:
        {date}.md   <- Human-readable insight
        {date}.csv  <- Raw evidence data

Triple-File Protocol (Source 5+):
    When raw_json is also provided:
        {date}.json <- Full structured payload (for book_builder / Source 6)

Storage layout (Project-First Architecture):
    storage/
        {project_slug}/          <- One folder per project (e.g. baby_bowl)
            0_catalog_insight/   <- Source 0 (Catalog Insight)
            1_keyword_traffic/   <- Source 1 (Keyword Traffic)
            2_review_analysis/   <- Source 2 (Review Analysis)
            3_rufus_defense/     <- Source 3 (Rufus)
            5_webmaster/         <- Source 5 (Webmaster)
            6_seo_writer/        <- Source 6 (SEO Writer)

Legacy flat layout (backward-compat, still supported for old saves):
    storage/
        0_catalog_insight/
        99_uncategorized/
"""

from __future__ import annotations

import os
import re
import shutil
from datetime import datetime

_STORAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "storage")
_DEFAULT_CATEGORY = "99_uncategorized"


def slugify_project_name(name: str) -> str:
    """
    Convert a project name to a filesystem-safe lowercase slug.

    Example: "Garlic Press Launch" → "garlic_press_launch"
    Used by top_bar.py (to set session_state["project_slug"]) and
    by save_insight callers (via st.session_state["project_slug"]).
    """
    return _slugify(name)


class KnowledgeManager:
    """
    Generic Hub — manages folders (categories) and Markdown files.

    No business logic. Accepts pre-formatted Markdown strings.

    Project-First Architecture:
        save_insight(..., project_slug="baby_bowl") writes to
        storage/baby_bowl/{subfolder}/{filename}.md

        Omitting project_slug (or passing "") falls back to the old
        flat layout: storage/{subfolder}/{filename}.md
    """

    def __init__(self):
        os.makedirs(_STORAGE_DIR, exist_ok=True)
        self._migrate_root_files()

    # ------------------------------------------------------------------
    # Category (folder) management
    # ------------------------------------------------------------------

    def list_categories(self) -> list[str]:
        """Return sorted list of top-level folder names inside storage/."""
        return sorted(
            entry for entry in os.listdir(_STORAGE_DIR)
            if os.path.isdir(os.path.join(_STORAGE_DIR, entry))
        )

    def create_category(self, name: str) -> bool:
        """
        Create a new category folder. Returns True if created.

        Sanitizes the name to be filesystem-safe.
        """
        safe = _slugify(name)
        if not safe:
            return False
        cat_dir = os.path.join(_STORAGE_DIR, safe)
        if os.path.exists(cat_dir):
            return False
        os.makedirs(cat_dir)
        return True

    def rename_category(self, old_name: str, new_name: str) -> bool:
        """Rename a category folder. Returns True if renamed."""
        old_dir = os.path.join(_STORAGE_DIR, old_name)
        safe_new = _slugify(new_name)
        if not safe_new or not os.path.isdir(old_dir):
            return False
        new_dir = os.path.join(_STORAGE_DIR, safe_new)
        if os.path.exists(new_dir):
            return False
        os.rename(old_dir, new_dir)
        return True

    # ------------------------------------------------------------------
    # Project folder management (Project-First Architecture)
    # ------------------------------------------------------------------

    def get_project_folder(self, project_slug: str) -> str:
        """Return the absolute path to a project's storage folder."""
        return os.path.join(_STORAGE_DIR, project_slug)

    def rename_project_folder(self, old_slug: str, new_slug: str) -> bool:
        """
        Rename a project's top-level storage folder.

        Args:
            old_slug: Current project slug (lowercase_underscores).
            new_slug: New project slug.

        Returns:
            True if the folder was renamed; False if source missing
            or destination already exists.
        """
        old_dir = os.path.join(_STORAGE_DIR, old_slug)
        new_dir = os.path.join(_STORAGE_DIR, new_slug)
        if not os.path.isdir(old_dir):
            return False          # nothing to rename (no saves yet — OK, not an error)
        if os.path.exists(new_dir):
            return False
        os.rename(old_dir, new_dir)
        return True

    def delete_project_folder(self, project_slug: str) -> bool:
        """
        Permanently delete a project's storage folder and ALL its contents.

        Uses shutil.rmtree — irreversible. Caller is responsible for
        confirming with the user before calling this.

        Returns:
            True if the folder existed and was deleted; False if not found.
        """
        target = os.path.join(_STORAGE_DIR, project_slug)
        if not os.path.isdir(target):
            return False
        shutil.rmtree(target)
        return True

    # ------------------------------------------------------------------
    # Insight (file) management
    # ------------------------------------------------------------------

    def save_insight(
        self,
        subfolder: str,
        filename: str,
        content: str,
        dataframe=None,
        raw_json: str | None = None,
        also_export_to: str | None = None,
        project_slug: str | None = None,
    ) -> str:
        """
        Save a Markdown string to storage.

        Path resolution:
            project_slug set → storage/{project_slug}/{subfolder}/{filename}
            project_slug None/""  → storage/{subfolder}/{filename}  (legacy)

        Triple-File Protocol (when both dataframe and raw_json are provided):
            {filename}.md   — Human-readable AI report
            {filename}.csv  — Tabular keyword/signal data (paired with MD)
            {filename}.json — Complete raw structured data (for Source 6 ingestion)

        Dual-Save Protocol (PM Decision #7):
            When also_export_to is provided, all written files are ALSO copied
            to that directory. Use this to keep data/raw_zeabur_exports/ in sync
            so book_builder always has the latest system runs to process.
            Pass: also_export_to=RAW_EXPORT_DIR (see constant in each page module).

        Args:
            subfolder:      Target subfolder (created if missing).
                            e.g. '0_catalog_insight', '5_webmaster'.
            filename:       File name WITHOUT extension (e.g. 'site_gsc_7d_2026-02-21').
                            The .md suffix is added automatically if missing.
            content:        Pre-formatted Markdown string.
            dataframe:      Optional pandas DataFrame to save as paired CSV.
            raw_json:       Optional JSON string to save as paired .json file.
                            Pass json.dumps(full_data_dict, indent=2, default=str).
            also_export_to: Optional directory path for Dual-Save mirror.
            project_slug:   Optional project slug (from st.session_state["project_slug"]).
                            Enables Project-First storage architecture.
                            Use slugify_project_name(project_name) to generate.

        Returns:
            The base filename that was written (with .md extension).
        """
        # Resolve destination directory
        if project_slug:
            dest_dir = os.path.join(_STORAGE_DIR, project_slug, subfolder)
        else:
            dest_dir = os.path.join(_STORAGE_DIR, subfolder)
        os.makedirs(dest_dir, exist_ok=True)

        # Normalise filename — always ends in .md
        if not filename.endswith(".md"):
            filename = filename + ".md"

        # Save Markdown
        filepath = os.path.join(dest_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        # Twin-File Protocol: save paired CSV
        if dataframe is not None:
            csv_filename = filename.replace(".md", ".csv")
            csv_path = os.path.join(dest_dir, csv_filename)
            dataframe.to_csv(csv_path, index=False)

        # Triple-File Protocol: save raw JSON for downstream consumers (Source 6)
        if raw_json is not None:
            json_filename = filename.replace(".md", ".json")
            json_path = os.path.join(dest_dir, json_filename)
            with open(json_path, "w", encoding="utf-8") as f:
                f.write(raw_json)

        # Dual-Save Protocol: mirror all written files to export directory
        if also_export_to:
            os.makedirs(also_export_to, exist_ok=True)
            with open(os.path.join(also_export_to, filename), "w", encoding="utf-8") as f:
                f.write(content)
            if dataframe is not None:
                csv_filename = filename.replace(".md", ".csv")
                dataframe.to_csv(os.path.join(also_export_to, csv_filename), index=False)
            if raw_json is not None:
                json_filename = filename.replace(".md", ".json")
                with open(os.path.join(also_export_to, json_filename), "w", encoding="utf-8") as f:
                    f.write(raw_json)

        return filename

    def list_insights(self) -> dict[str, list[dict]]:
        """
        Return all saved insights grouped by category.

        Handles both storage layouts transparently:
          • Old flat:   storage/2_review_analysis/file.md
                        → key: "2_review_analysis"
          • New nested: storage/baby_bowl/2_review_analysis/file.md
                        → key: "baby_bowl/<sep>2_review_analysis"

        Returns:
            {
              '2_review_analysis': [
                {'filename': '...', 'size_bytes': 1234, 'modified': '...'},
              ],
              'baby_bowl/2_review_analysis': [...],
            }
        """
        grouped: dict[str, list[dict]] = {}

        for entry in sorted(os.listdir(_STORAGE_DIR)):
            entry_dir = os.path.join(_STORAGE_DIR, entry)
            if not os.path.isdir(entry_dir):
                continue

            dir_items = os.listdir(entry_dir)
            has_direct_mds = any(f.endswith(".md") for f in dir_items)

            if has_direct_mds:
                # OLD flat structure: this dir is a source subfolder
                grouped[entry] = _collect_md_files(entry_dir)
            else:
                # NEW project-first structure: this dir is a project slug
                # Recurse one level into source subfolders
                for sub in sorted(dir_items):
                    sub_dir = os.path.join(entry_dir, sub)
                    if not os.path.isdir(sub_dir):
                        continue
                    cat_key = os.path.join(entry, sub)  # OS-native separator
                    grouped[cat_key] = _collect_md_files(sub_dir)

        return grouped

    def get_insight(self, category: str, filename: str) -> str:
        """Read and return the Markdown content of a saved insight."""
        fpath = os.path.join(_STORAGE_DIR, category, filename)
        with open(fpath, "r", encoding="utf-8") as f:
            return f.read()

    def delete_insight(self, category: str, filename: str) -> bool:
        """Delete a saved insight (MD only). Returns True if removed."""
        fpath = os.path.join(_STORAGE_DIR, category, filename)
        if os.path.exists(fpath):
            os.remove(fpath)
            return True
        return False

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def make_filename(title: str) -> str:
        """
        Generate a dated, case-preserving filename from a title.

        Twin-File Protocol naming: {Project_Name}_{YYYY-MM-DD}.md
        Example: "Baby Teether Strategy" -> "Baby_Teether_Strategy_2026-02-08.md"
        """
        slug = _title_slug(title)
        date_str = datetime.now().strftime("%Y-%m-%d")
        return f"{slug}_{date_str}.md"

    # ------------------------------------------------------------------
    # Migration — one-time move of root-level .md files
    # ------------------------------------------------------------------

    def _migrate_root_files(self) -> None:
        """Move any .md files sitting in the root storage/ into 99_uncategorized/."""
        root_mds = [
            f for f in os.listdir(_STORAGE_DIR)
            if f.endswith(".md") and os.path.isfile(os.path.join(_STORAGE_DIR, f))
        ]
        if not root_mds:
            return

        dest = os.path.join(_STORAGE_DIR, _DEFAULT_CATEGORY)
        os.makedirs(dest, exist_ok=True)

        for fname in root_mds:
            src = os.path.join(_STORAGE_DIR, fname)
            dst = os.path.join(dest, fname)
            shutil.move(src, dst)


# ------------------------------------------------------------------
# Module-level helpers
# ------------------------------------------------------------------

def _slugify(text: str) -> str:
    """Convert a title to a lowercase filesystem-safe slug."""
    s = text.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "_", s)
    return s[:80]


def _title_slug(text: str) -> str:
    """Convert a title to a filesystem-safe slug, preserving original casing."""
    s = text.strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "_", s)
    return s[:80]


def _collect_md_files(dir_path: str) -> list[dict]:
    """Return sorted (desc) list of .md file metadata dicts from a directory."""
    files: list[dict] = []
    for fname in sorted(os.listdir(dir_path), reverse=True):
        if not fname.endswith(".md"):
            continue
        fpath = os.path.join(dir_path, fname)
        stat = os.stat(fpath)
        files.append({
            "filename": fname,
            "size_bytes": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).strftime(
                "%Y-%m-%d %H:%M"
            ),
        })
    return files
